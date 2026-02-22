"""\
Movie interactions API routes.

Implements TZ requirements:
- Like/Dislike movies
- Comments (with replies)
- Like comments (for notifications)
- Favorites
- Ratings (1-10)
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.database.models import UserModel
from src.schemas.movie_interactions import (
    MovieLikeCreateSchema,
    MovieLikeResponseSchema,
    MovieLikeStatsSchema,
    MovieCommentCreateSchema,
    MovieCommentResponseSchema,
    MovieCommentListResponseSchema,
    MovieCommentUpdateSchema,
    MovieFavoriteAddSchema,
    MovieFavoriteRemoveSchema,
    FavoritesListResponseSchema,
    MovieRatingCreateSchema,
    MovieRatingResponseSchema,
    MovieRatingStatsSchema,
    CommentLikeResponseSchema,
)
from src.security.http import get_current_active_user
from src.services.movie_interaction_service import MovieInteractionService


router = APIRouter()


# ===== Likes / Dislikes =====


@router.post(
    "/movies/{movie_id}/like/",
    response_model=MovieLikeResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Like or dislike a movie",
)
async def like_movie(
    movie_id: int,
    payload: MovieLikeCreateSchema,
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MovieLikeResponseSchema:
    like = await MovieInteractionService.toggle_like(
        movie_id=movie_id,
        user_id=current_user.id,
        is_like=payload.is_like,
        db=db,
    )
    return MovieLikeResponseSchema.model_validate(like)


@router.delete(
    "/movies/{movie_id}/like/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove like/dislike from a movie",
)
async def remove_movie_like(
    movie_id: int,
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await MovieInteractionService.remove_like(movie_id=movie_id, user_id=current_user.id, db=db)


@router.get(
    "/movies/{movie_id}/likes/",
    response_model=MovieLikeStatsSchema,
    status_code=status.HTTP_200_OK,
    summary="Get like/dislike statistics for a movie",
)
async def get_movie_like_stats(
    movie_id: int,
    current_user: Optional[UserModel] = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MovieLikeStatsSchema:
    stats = await MovieInteractionService.get_like_stats(
        movie_id=movie_id,
        user_id=current_user.id if current_user else None,
        db=db,
    )
    return MovieLikeStatsSchema(**stats)


# ===== Comments =====


@router.post(
    "/movies/{movie_id}/comments/",
    response_model=MovieCommentResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a comment (or reply) on a movie",
)
async def create_comment(
    movie_id: int,
    payload: MovieCommentCreateSchema,
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MovieCommentResponseSchema:
    comment = await MovieInteractionService.create_comment(
        movie_id=movie_id,
        user_id=current_user.id,
        content=payload.content,
        parent_id=payload.parent_id,
        db=db,
        notify=True,
    )
    return MovieCommentResponseSchema.model_validate(comment)


@router.get(
    "/movies/{movie_id}/comments/",
    response_model=MovieCommentListResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Get movie comments with pagination",
)
async def get_movie_comments(
    movie_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> MovieCommentListResponseSchema:
    comments, total = await MovieInteractionService.get_movie_comments(
        movie_id=movie_id,
        db=db,
        page=page,
        per_page=per_page,
    )
    total_pages = (total + per_page - 1) // per_page if total else 0
    return MovieCommentListResponseSchema(
        comments=[MovieCommentResponseSchema.model_validate(c) for c in comments],
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        total_items=total,
    )


@router.patch(
    "/comments/{comment_id}/",
    response_model=MovieCommentResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Update own comment",
)
async def update_comment(
    comment_id: int,
    payload: MovieCommentUpdateSchema,
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MovieCommentResponseSchema:
    comment = await MovieInteractionService.update_comment(
        comment_id=comment_id,
        user_id=current_user.id,
        content=payload.content,
        db=db,
    )
    return MovieCommentResponseSchema.model_validate(comment)


@router.delete(
    "/comments/{comment_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete own comment",
)
async def delete_comment(
    comment_id: int,
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await MovieInteractionService.delete_comment(comment_id=comment_id, user_id=current_user.id, db=db)


@router.post(
    "/comments/{comment_id}/like/",
    response_model=CommentLikeResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Like a comment (toggle)",
)
async def toggle_comment_like(
    comment_id: int,
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CommentLikeResponseSchema:
    result = await MovieInteractionService.toggle_comment_like(
        comment_id=comment_id,
        user_id=current_user.id,
        db=db,
        notify=True,
    )
    return CommentLikeResponseSchema(**result)


# ===== Favorites =====


@router.post(
    "/movies/{movie_id}/favorites/",
    response_model=MovieFavoriteAddSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Add movie to favorites",
)
async def add_to_favorites(
    movie_id: int,
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MovieFavoriteAddSchema:
    await MovieInteractionService.add_to_favorites(movie_id=movie_id, user_id=current_user.id, db=db)
    return MovieFavoriteAddSchema()


@router.delete(
    "/movies/{movie_id}/favorites/",
    response_model=MovieFavoriteRemoveSchema,
    status_code=status.HTTP_200_OK,
    summary="Remove movie from favorites",
)
async def remove_from_favorites(
    movie_id: int,
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MovieFavoriteRemoveSchema:
    await MovieInteractionService.remove_from_favorites(movie_id=movie_id, user_id=current_user.id, db=db)
    return MovieFavoriteRemoveSchema()


@router.get(
    "/favorites/",
    response_model=FavoritesListResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="List favorite movies",
)
async def list_favorites(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    search: Optional[str] = Query(None, description="Search by title/description/actor/director"),
    year: Optional[int] = Query(None, description="Filter by release year"),
    imdb_min: Optional[float] = Query(None, description="Filter by min IMDb"),
    sort_by: str = Query("added_at", description="Sort by: added_at|price|year|imdb"),
    sort_dir: str = Query("desc", description="asc|desc"),
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> FavoritesListResponseSchema:
    items, total = await MovieInteractionService.list_favorites(
        user_id=current_user.id,
        db=db,
        page=page,
        per_page=per_page,
        search=search,
        year=year,
        imdb_min=imdb_min,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    total_pages = (total + per_page - 1) // per_page if total else 0
    return FavoritesListResponseSchema(
        favorites=items,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        total_items=total,
    )


# ===== Ratings =====


@router.post(
    "/movies/{movie_id}/rating/",
    response_model=MovieRatingResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Rate a movie (1-10)",
)
async def rate_movie(
    movie_id: int,
    payload: MovieRatingCreateSchema,
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MovieRatingResponseSchema:
    rating = await MovieInteractionService.set_rating(
        movie_id=movie_id,
        user_id=current_user.id,
        rating=payload.rating,
        db=db,
    )
    return MovieRatingResponseSchema.model_validate(rating)


@router.delete(
    "/movies/{movie_id}/rating/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove rating",
)
async def remove_rating(
    movie_id: int,
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await MovieInteractionService.remove_rating(movie_id=movie_id, user_id=current_user.id, db=db)


@router.get(
    "/movies/{movie_id}/rating/",
    response_model=MovieRatingStatsSchema,
    status_code=status.HTTP_200_OK,
    summary="Get rating stats",
)
async def rating_stats(
    movie_id: int,
    current_user: Optional[UserModel] = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MovieRatingStatsSchema:
    stats = await MovieInteractionService.get_rating_stats(
        movie_id=movie_id,
        user_id=current_user.id if current_user else None,
        db=db,
    )
    return MovieRatingStatsSchema(**stats)
