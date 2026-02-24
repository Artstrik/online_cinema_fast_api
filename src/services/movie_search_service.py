"""
Business logic for movie search, filtering, and sorting.
"""
from typing import List, Optional, Tuple
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.database.models import (
    MovieModel,
    GenreModel,
    ActorModel,
    DirectorModel,
    CertificationModel,
    MoviesGenresModel,
    ActorsMoviesModel,
    DirectorsMoviesModel,
)


class MovieSearchService:
    """Service for advanced movie search and filtering."""

    @staticmethod
    async def search_and_filter_movies(
        db: AsyncSession,
        search: Optional[str] = None,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
        imdb_min: Optional[float] = None,
        imdb_max: Optional[float] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        genre_ids: Optional[List[int]] = None,
        certification_ids: Optional[List[int]] = None,
        sort_by: str = "id",
        sort_order: str = "desc",
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[MovieModel], int]:
        """
        Advanced movie search with filtering and sorting.

        Args:
            db: Database session
            search: Search query (title, description, actor, director)
            year_min: Minimum release year
            year_max: Maximum release year
            imdb_min: Minimum IMDb rating
            imdb_max: Maximum IMDb rating
            price_min: Minimum price
            price_max: Maximum price
            genre_ids: List of genre IDs to filter by
            certification_ids: List of certification IDs to filter by
            sort_by: Field to sort by (id, year, imdb, price, created_at)
            sort_order: Sort order (asc, desc)
            page: Page number
            per_page: Items per page

        Returns:
            Tuple of (movies list, total count)
        """
        # Build base query
        query = select(MovieModel).distinct()

        # Apply search
        if search:
            search_term = f"%{search.lower()}%"

            # Search in movie name and description
            search_conditions = [
                func.lower(MovieModel.name).like(search_term),
                func.lower(MovieModel.description).like(search_term),
            ]

            # Search in actors
            actor_subquery = (
                select(ActorsMoviesModel.c.movie_id)
                .join(ActorModel, ActorModel.id == ActorsMoviesModel.c.actor_id)
                .where(func.lower(ActorModel.name).like(search_term))
            )
            search_conditions.append(MovieModel.id.in_(actor_subquery))

            # Search in directors
            director_subquery = (
                select(DirectorsMoviesModel.c.movie_id)
                .join(
                    DirectorModel,
                    DirectorModel.id == DirectorsMoviesModel.c.director_id,
                )
                .where(func.lower(DirectorModel.name).like(search_term))
            )
            search_conditions.append(MovieModel.id.in_(director_subquery))

            query = query.where(or_(*search_conditions))

        # Apply filters
        filters = []

        if year_min is not None:
            filters.append(MovieModel.year >= year_min)

        if year_max is not None:
            filters.append(MovieModel.year <= year_max)

        if imdb_min is not None:
            filters.append(MovieModel.imdb >= imdb_min)

        if imdb_max is not None:
            filters.append(MovieModel.imdb <= imdb_max)

        if price_min is not None:
            filters.append(MovieModel.price >= price_min)

        if price_max is not None:
            filters.append(MovieModel.price <= price_max)

        if genre_ids:
            genre_subquery = select(MoviesGenresModel.c.movie_id).where(
                MoviesGenresModel.c.genre_id.in_(genre_ids)
            )
            filters.append(MovieModel.id.in_(genre_subquery))

        if certification_ids:
            filters.append(MovieModel.certification_id.in_(certification_ids))

        if filters:
            query = query.where(and_(*filters))

        # Count total results
        count_query = select(func.count()).select_from(query.subquery())
        result = await db.execute(count_query)
        total = result.scalar() or 0

        # Apply sorting
        sort_field = getattr(MovieModel, sort_by, MovieModel.id)
        if sort_order.lower() == "asc":
            query = query.order_by(sort_field.asc())
        else:
            query = query.order_by(sort_field.desc())

        # Apply pagination
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        # Load relationships
        query = query.options(
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.directors),
            joinedload(MovieModel.certification),
        )

        # Execute query
        result = await db.execute(query)
        movies = result.scalars().unique().all()

        return list(movies), total

    @staticmethod
    async def get_genres_with_count(db: AsyncSession) -> List[dict]:
        """
        Get all genres with movie count.

        Returns:
            List of dicts with genre info and movie count
        """
        query = (
            select(
                GenreModel.id,
                GenreModel.name,
                func.count(MoviesGenresModel.c.movie_id).label("movie_count"),
            )
            .outerjoin(MoviesGenresModel, GenreModel.id == MoviesGenresModel.c.genre_id)
            .group_by(GenreModel.id, GenreModel.name)
            .order_by(GenreModel.name)
        )

        result = await db.execute(query)
        genres = result.all()

        return [
            {"id": genre.id, "name": genre.name, "movie_count": genre.movie_count}
            for genre in genres
        ]

    @staticmethod
    async def get_movies_by_genre(
        db: AsyncSession, genre_id: int, page: int = 1, per_page: int = 20
    ) -> Tuple[List[MovieModel], int]:
        """
        Get movies by genre with pagination.

        Args:
            db: Database session
            genre_id: Genre ID
            page: Page number
            per_page: Items per page

        Returns:
            Tuple of (movies list, total count)
        """
        # Count total movies in genre
        count_query = select(func.count(MoviesGenresModel.c.movie_id)).where(
            MoviesGenresModel.c.genre_id == genre_id
        )
        result = await db.execute(count_query)
        total = result.scalar() or 0

        # Get movies
        offset = (page - 1) * per_page

        movie_ids_query = select(MoviesGenresModel.c.movie_id).where(
            MoviesGenresModel.c.genre_id == genre_id
        )

        query = (
            select(MovieModel)
            .where(MovieModel.id.in_(movie_ids_query))
            .options(
                joinedload(MovieModel.genres),
                joinedload(MovieModel.actors),
                joinedload(MovieModel.directors),
                joinedload(MovieModel.certification),
            )
            .order_by(MovieModel.id.desc())
            .offset(offset)
            .limit(per_page)
        )

        result = await db.execute(query)
        movies = result.scalars().unique().all()

        return list(movies), total

    @staticmethod
    async def get_certifications(db: AsyncSession) -> List[CertificationModel]:
        """Get all available certifications."""
        query = select(CertificationModel).order_by(CertificationModel.name)
        result = await db.execute(query)
        return list(result.scalars().all())
