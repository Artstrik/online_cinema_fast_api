"""
Business logic for movie interaction operations (likes, comments, favorites, ratings).
"""
from typing import List, Optional, Tuple
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from fastapi import HTTPException, status

from src.database.models import (
    MovieModel, MovieLikeModel, MovieCommentModel,
    MovieFavoriteModel, MovieRatingModel, UserModel
)


class MovieInteractionService:
    """Service for managing movie interaction operations."""

    # ===== LIKES =====

    @staticmethod
    async def toggle_like(
            movie_id: int,
            user_id: int,
            is_like: bool,
            db: AsyncSession
    ) -> MovieLikeModel:
        """
        Toggle like/dislike on a movie.

        Args:
            movie_id: Movie ID
            user_id: User ID
            is_like: True for like, False for dislike
            db: Database session

        Returns:
            Created or updated like
        """
        # Check movie exists
        stmt = select(MovieModel).where(MovieModel.id == movie_id)
        result = await db.execute(stmt)
        movie = result.scalars().first()

        if not movie:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Movie {movie_id} not found"
            )

        # Check if like already exists
        stmt = select(MovieLikeModel).where(
            MovieLikeModel.movie_id == movie_id,
            MovieLikeModel.user_id == user_id
        )
        result = await db.execute(stmt)
        existing_like = result.scalars().first()

        if existing_like:
            # Update existing like
            existing_like.is_like = is_like
            await db.commit()
            await db.refresh(existing_like)
            return existing_like
        else:
            # Create new like
            new_like = MovieLikeModel(
                movie_id=movie_id,
                user_id=user_id,
                is_like=is_like
            )
            db.add(new_like)
            await db.commit()
            await db.refresh(new_like)
            return new_like

    @staticmethod
    async def remove_like(
            movie_id: int,
            user_id: int,
            db: AsyncSession
    ) -> None:
        """Remove like/dislike from a movie."""
        stmt = select(MovieLikeModel).where(
            MovieLikeModel.movie_id == movie_id,
            MovieLikeModel.user_id == user_id
        )
        result = await db.execute(stmt)
        like = result.scalars().first()

        if not like:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Like not found"
            )

        await db.delete(like)
        await db.commit()

    @staticmethod
    async def get_like_stats(
            movie_id: int,
            user_id: Optional[int],
            db: AsyncSession
    ) -> dict:
        """Get like statistics for a movie."""
        # Count likes
        stmt = select(func.count(MovieLikeModel.id)).where(
            MovieLikeModel.movie_id == movie_id,
            MovieLikeModel.is_like == True
        )
        result = await db.execute(stmt)
        likes_count = result.scalar() or 0

        # Count dislikes
        stmt = select(func.count(MovieLikeModel.id)).where(
            MovieLikeModel.movie_id == movie_id,
            MovieLikeModel.is_like == False
        )
        result = await db.execute(stmt)
        dislikes_count = result.scalar() or 0

        # Get user's like if provided
        user_like = None
        if user_id:
            stmt = select(MovieLikeModel).where(
                MovieLikeModel.movie_id == movie_id,
                MovieLikeModel.user_id == user_id
            )
            result = await db.execute(stmt)
            like = result.scalars().first()
            if like:
                user_like = like.is_like

        return {
            "movie_id": movie_id,
            "likes_count": likes_count,
            "dislikes_count": dislikes_count,
            "user_like": user_like
        }

    # ===== COMMENTS =====

    @staticmethod
    async def create_comment(
            movie_id: int,
            user_id: int,
            content: str,
            parent_id: Optional[int],
            db: AsyncSession
    ) -> MovieCommentModel:
        """Create a comment on a movie."""
        # Check movie exists
        stmt = select(MovieModel).where(MovieModel.id == movie_id)
        result = await db.execute(stmt)
        if not result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Movie {movie_id} not found"
            )

        # Check parent comment exists if provided
        if parent_id:
            stmt = select(MovieCommentModel).where(MovieCommentModel.id == parent_id)
            result = await db.execute(stmt)
            if not result.scalars().first():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Parent comment {parent_id} not found"
                )

        comment = MovieCommentModel(
            movie_id=movie_id,
            user_id=user_id,
            content=content,
            parent_id=parent_id
        )
        db.add(comment)
        await db.commit()
        await db.refresh(comment)

        # Load relationships
        stmt = (
            select(MovieCommentModel)
            .options(joinedload(MovieCommentModel.user))
            .where(MovieCommentModel.id == comment.id)
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def get_movie_comments(
            movie_id: int,
            db: AsyncSession,
            page: int = 1,
            per_page: int = 20
    ) -> Tuple[List[MovieCommentModel], int]:
        """Get comments for a movie with pagination."""
        offset = (page - 1) * per_page

        # Count total comments (only root comments)
        stmt = select(func.count(MovieCommentModel.id)).where(
            MovieCommentModel.movie_id == movie_id,
            MovieCommentModel.parent_id == None
        )
        result = await db.execute(stmt)
        total = result.scalar() or 0

        # Get comments
        stmt = (
            select(MovieCommentModel)
            .options(
                joinedload(MovieCommentModel.user),
                joinedload(MovieCommentModel.replies)
            )
            .where(
                MovieCommentModel.movie_id == movie_id,
                MovieCommentModel.parent_id == None
            )
            .order_by(MovieCommentModel.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        result = await db.execute(stmt)
        comments = result.scalars().unique().all()

        return list(comments), total

    @staticmethod
    async def update_comment(
            comment_id: int,
            user_id: int,
            content: str,
            db: AsyncSession
    ) -> MovieCommentModel:
        """Update a comment."""
        stmt = select(MovieCommentModel).where(MovieCommentModel.id == comment_id)
        result = await db.execute(stmt)
        comment = result.scalars().first()

        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )

        if comment.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only edit your own comments"
            )

        comment.content = content
        await db.commit()
        await db.refresh(comment)
        return comment

    @staticmethod
    async def delete_comment(
            comment_id: int,
            user_id: int,
            db: AsyncSession
    ) -> None:
        """Delete a comment."""
        stmt = select(MovieCommentModel).where(MovieCommentModel.id == comment_id)
        result = await db.execute(stmt)
        comment = result.scalars().first()

        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )

        if comment.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own comments"
            )

        await db.delete(comment)
        await db.commit()

    # ===== FAVORITES =====

    @staticmethod
    async def add_to_favorites(
            movie_id: int,
            user_id: int,
            db: AsyncSession
    ) -> MovieFavoriteModel:
        """Add movie to favorites."""
        # Check movie exists
        stmt = select(MovieModel).where(MovieModel.id == movie_id)
        result = await db.execute(stmt)
        if not result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Movie {movie_id} not found"
            )

        # Check if already in favorites
        stmt = select(MovieFavoriteModel).where(
            MovieFavoriteModel.movie_id == movie_id,
            MovieFavoriteModel.user_id == user_id
        )
        result = await db.execute(stmt)
        if result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Movie already in favorites"
            )

        favorite = MovieFavoriteModel(
            movie_id=movie_id,
            user_id=user_id
        )
        db.add(favorite)
        await db.commit()
        await db.refresh(favorite)
        return favorite

    @staticmethod
    async def remove_from_favorites(
            movie_id: int,
            user_id: int,
            db: AsyncSession
    ) -> None:
        """Remove movie from favorites."""
        stmt = select(MovieFavoriteModel).where(
            MovieFavoriteModel.movie_id == movie_id,
            MovieFavoriteModel.user_id == user_id
        )
        result = await db.execute(stmt)
        favorite = result.scalars().first()

        if not favorite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Movie not in favorites"
            )

        await db.delete(favorite)
        await db.commit()

    @staticmethod
    async def get_user_favorites(
            user_id: int,
            db: AsyncSession,
            page: int = 1,
            per_page: int = 20
    ) -> Tuple[List[MovieFavoriteModel], int]:
        """Get user's favorite movies."""
        offset = (page - 1) * per_page

        # Count total
        stmt = select(func.count(MovieFavoriteModel.id)).where(
            MovieFavoriteModel.user_id == user_id
        )
        result = await db.execute(stmt)
        total = result.scalar() or 0

        # Get favorites
        stmt = (
            select(MovieFavoriteModel)
            .options(joinedload(MovieFavoriteModel.movie))
            .where(MovieFavoriteModel.user_id == user_id)
            .order_by(MovieFavoriteModel.added_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        result = await db.execute(stmt)
        favorites = result.scalars().unique().all()

        return list(favorites), total

    # ===== RATINGS =====

    @staticmethod
    async def rate_movie(
            movie_id: int,
            user_id: int,
            rating: int,
            db: AsyncSession
    ) -> MovieRatingModel:
        """Rate a movie (1-10 scale)."""
        # Check movie exists
        stmt = select(MovieModel).where(MovieModel.id == movie_id)
        result = await db.execute(stmt)
        if not result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Movie {movie_id} not found"
            )

        # Check if rating already exists
        stmt = select(MovieRatingModel).where(
            MovieRatingModel.movie_id == movie_id,
            MovieRatingModel.user_id == user_id
        )
        result = await db.execute(stmt)
        existing_rating = result.scalars().first()

        if existing_rating:
            # Update existing rating
            existing_rating.rating = rating
            await db.commit()
            await db.refresh(existing_rating)
            return existing_rating
        else:
            # Create new rating
            new_rating = MovieRatingModel(
                movie_id=movie_id,
                user_id=user_id,
                rating=rating
            )
            db.add(new_rating)
            await db.commit()
            await db.refresh(new_rating)
            return new_rating

    @staticmethod
    async def get_rating_stats(
            movie_id: int,
            user_id: Optional[int],
            db: AsyncSession
    ) -> dict:
        """Get rating statistics for a movie."""
        # Calculate average rating
        stmt = select(func.avg(MovieRatingModel.rating)).where(
            MovieRatingModel.movie_id == movie_id
        )
        result = await db.execute(stmt)
        avg_rating = result.scalar()

        # Count total ratings
        stmt = select(func.count(MovieRatingModel.id)).where(
            MovieRatingModel.movie_id == movie_id
        )
        result = await db.execute(stmt)
        total_ratings = result.scalar() or 0

        # Get user's rating if provided
        user_rating = None
        if user_id:
            stmt = select(MovieRatingModel).where(
                MovieRatingModel.movie_id == movie_id,
                MovieRatingModel.user_id == user_id
            )
            result = await db.execute(stmt)
            rating = result.scalars().first()
            if rating:
                user_rating = rating.rating

        return {
            "movie_id": movie_id,
            "average_rating": float(avg_rating) if avg_rating else None,
            "total_ratings": total_ratings,
            "user_rating": user_rating
        }
