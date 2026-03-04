"""Movies API routes.

Aligned to TZ (technical specification) for the Movies module:
- Browse catalog with pagination
- View movie details
- Filter and sort
- Search by title/description/star/director
- Moderator/Admin: CRUD for movies
- Genres list with movie counts

Notes:
- DB layer currently uses ActorModel for stars.
  API uses the term "stars" to match TZ.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, or_, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.database import (
    get_db,
    MovieModel,
)
from src.database.models import UserGroupEnum
from src.database.models.movies import (
    GenreModel,
    DirectorModel,
    ActorModel,
    CertificationModel,
    MoviesGenresModel,
    DirectorsMoviesModel,
    ActorsMoviesModel,
)
from src.schemas.movies import (
    MovieListResponseSchema,
    MovieListItemSchema,
    MovieDetailSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
    GenreListWithCountResponseSchema,
    GenreWithCountSchema,
    SortByMovies,
    SortOrder,
)
from src.security.http import require_roles

router = APIRouter()


def _apply_movie_sort(stmt, sort_by: SortByMovies, order: SortOrder):
    column_map = {
        "year": MovieModel.year,
        "imdb": MovieModel.imdb,
        "votes": MovieModel.votes,
        "price": MovieModel.price,
        "name": MovieModel.name,
    }
    col = column_map.get(sort_by, MovieModel.id)
    if order == "desc":
        return stmt.order_by(col.desc(), MovieModel.id.desc())
    return stmt.order_by(col.asc(), MovieModel.id.asc())


@router.get(
    "/movies/",
    response_model=MovieListResponseSchema,
    summary="Get a paginated list of movies",
)
async def get_movie_list(
    page: int = Query(1, ge=1, description="Page number (1-based index)"),
    per_page: int = Query(10, ge=1, le=50, description="Items per page"),
    q: Optional[str] = Query(None, description="Search query (title/description/star/director)"),
    year_from: Optional[int] = Query(None, ge=1888, le=2200),
    year_to: Optional[int] = Query(None, ge=1888, le=2200),
    imdb_min: Optional[float] = Query(None, ge=0, le=10),
    price_min: Optional[Decimal] = Query(None, ge=0),
    price_max: Optional[Decimal] = Query(None, ge=0),
    genre: Optional[str] = Query(None, description="Filter by genre name"),
    director: Optional[str] = Query(None, description="Filter by director name"),
    star: Optional[str] = Query(None, description="Filter by star name"),
    certification: Optional[str] = Query(None, description="Filter by certification name"),
    sort_by: SortByMovies = Query("year"),
    order: SortOrder = Query("desc"),
    db: AsyncSession = Depends(get_db),
) -> MovieListResponseSchema:
    offset = (page - 1) * per_page

    stmt = select(MovieModel)

    # Filtering
    filters = []
    if year_from is not None:
        filters.append(MovieModel.year >= year_from)
    if year_to is not None:
        filters.append(MovieModel.year <= year_to)
    if imdb_min is not None:
        filters.append(MovieModel.imdb >= imdb_min)
    if price_min is not None:
        filters.append(MovieModel.price >= price_min)
    if price_max is not None:
        filters.append(MovieModel.price <= price_max)

    if certification:
        stmt = stmt.join(CertificationModel, MovieModel.certification_id == CertificationModel.id)
        filters.append(func.lower(CertificationModel.name) == certification.strip().lower())

    if genre:
        stmt = stmt.join(MoviesGenresModel).join(GenreModel)
        filters.append(func.lower(GenreModel.name) == genre.strip().lower())

    if director:
        stmt = stmt.join(DirectorsMoviesModel).join(DirectorModel)
        filters.append(func.lower(DirectorModel.name) == director.strip().lower())

    if star:
        stmt = stmt.join(ActorsMoviesModel).join(ActorModel)
        filters.append(func.lower(ActorModel.name) == star.strip().lower())

    if q:
        query = f"%{q.strip()}%"
        # left joins for star/director search
        stmt = stmt.outerjoin(ActorsMoviesModel).outerjoin(ActorModel)
        stmt = stmt.outerjoin(DirectorsMoviesModel).outerjoin(DirectorModel)
        filters.append(
            or_(
                MovieModel.name.ilike(query),
                MovieModel.description.ilike(query),
                ActorModel.name.ilike(query),
                DirectorModel.name.ilike(query),
            )
        )

    if filters:
        stmt = stmt.where(and_(*filters))

    # Remove duplicates if joins produced them
    stmt = stmt.distinct(MovieModel.id)

    # Total count
    count_stmt = select(func.count(func.distinct(MovieModel.id))).select_from(stmt.subquery())
    total_items = (await db.execute(count_stmt)).scalar() or 0
    if total_items == 0:
        return MovieListResponseSchema(
            movies=[],
            prev_page=None,
            next_page=None,
            total_pages=0,
            total_items=0,
        )

    stmt = _apply_movie_sort(stmt, sort_by=sort_by, order=order)
    stmt = stmt.offset(offset).limit(per_page)

    movies = (await db.execute(stmt)).scalars().all()
    movie_list = [MovieListItemSchema.model_validate(m) for m in movies]

    total_pages = (total_items + per_page - 1) // per_page

    return MovieListResponseSchema(
        movies=movie_list,
        prev_page=f"/api/v1/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None,
        next_page=f"/api/v1/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailSchema,
    summary="Get movie details by ID",
)
async def get_movie_by_id(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
) -> MovieDetailSchema:
    stmt = (
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            joinedload(MovieModel.genres),
            joinedload(MovieModel.directors),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.certification),
        )
    )
    movie = (await db.execute(stmt)).scalars().first()
    if not movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found.")

    # Map actors -> stars in schema via alias property in schema (stars uses from_attributes)
    # SQLAlchemy model has .actors; pydantic will not map automatically, so we build dict manually.
    payload = MovieDetailSchema.model_validate(movie).model_dump()
    payload["stars"] = [
        {"id": a.id, "name": a.name}
        for a in getattr(movie, "actors", [])
    ]

    return MovieDetailSchema(**payload)


@router.get(
    "/genres/",
    response_model=GenreListWithCountResponseSchema,
    summary="List genres with movie counts",
)
async def list_genres_with_counts(
    db: AsyncSession = Depends(get_db),
) -> GenreListWithCountResponseSchema:
    stmt = (
        select(
            GenreModel.id,
            GenreModel.name,
            func.count(MoviesGenresModel.c.movie_id).label("movies_count"),
        )
        .outerjoin(MoviesGenresModel, MoviesGenresModel.c.genre_id == GenreModel.id)
        .group_by(GenreModel.id)
        .order_by(GenreModel.name.asc())
    )
    rows = (await db.execute(stmt)).all()

    genres = [
        GenreWithCountSchema(id=row.id, name=row.name, movies_count=row.movies_count)
        for row in rows
    ]
    return GenreListWithCountResponseSchema(genres=genres)


@router.post(
    "/movies/",
    response_model=MovieDetailSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create movie (Moderator/Admin)",
)
async def create_movie(
    data: MovieCreateSchema,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles(UserGroupEnum.MODERATOR, UserGroupEnum.ADMIN)),
) -> MovieDetailSchema:
    # Unique constraint required by TZ: (name, year, time)
    existing = (
        await db.execute(
            select(MovieModel).where(
                MovieModel.name == data.name,
                MovieModel.year == data.year,
                MovieModel.time == data.time,
            )
        )
    ).scalars().first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Movie already exists.")

    # certification
    cert = (
        await db.execute(
            select(CertificationModel).where(func.lower(CertificationModel.name) == data.certification.lower())
        )
    ).scalars().first()
    if not cert:
        cert = CertificationModel(name=data.certification)
        db.add(cert)
        await db.flush()

    # genres
    genres: list[GenreModel] = []
    for g in data.genres:
        if not g:
            continue
        genre = (
            await db.execute(select(GenreModel).where(func.lower(GenreModel.name) == g.lower()))
        ).scalars().first()
        if not genre:
            genre = GenreModel(name=g)
            db.add(genre)
            await db.flush()
        genres.append(genre)

    # directors
    directors: list[DirectorModel] = []
    for d in data.directors:
        if not d:
            continue
        director = (
            await db.execute(select(DirectorModel).where(func.lower(DirectorModel.name) == d.lower()))
        ).scalars().first()
        if not director:
            director = DirectorModel(name=d)
            db.add(director)
            await db.flush()
        directors.append(director)

    # stars (actors table)
    stars: list[ActorModel] = []
    for s in data.stars:
        if not s:
            continue
        star = (
            await db.execute(select(ActorModel).where(func.lower(ActorModel.name) == s.lower()))
        ).scalars().first()
        if not star:
            star = ActorModel(name=s)
            db.add(star)
            await db.flush()
        stars.append(star)

    movie = MovieModel(
        name=data.name,
        year=data.year,
        time=data.time,
        imdb=data.imdb,
        votes=data.votes,
        meta_score=data.meta_score,
        gross=data.gross,
        description=data.description,
        price=data.price,
        certification=cert,
        genres=genres,
        directors=directors,
        actors=stars,
    )

    db.add(movie)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid movie data.")

    await db.refresh(movie)

    # Build detail with stars mapping
    stmt = (
        select(MovieModel)
        .where(MovieModel.id == movie.id)
        .options(
            joinedload(MovieModel.genres),
            joinedload(MovieModel.directors),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.certification),
        )
    )
    movie = (await db.execute(stmt)).scalars().first()

    payload = MovieDetailSchema.model_validate(movie).model_dump()
    payload["stars"] = [{"id": a.id, "name": a.name} for a in getattr(movie, "actors", [])]
    return MovieDetailSchema(**payload)


@router.patch(
    "/movies/{movie_id}/",
    response_model=MovieDetailSchema,
    summary="Update movie (Moderator/Admin)",
)
async def update_movie(
    movie_id: int,
    data: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles(UserGroupEnum.MODERATOR, UserGroupEnum.ADMIN)),
) -> MovieDetailSchema:
    movie = (await db.execute(select(MovieModel).where(MovieModel.id == movie_id))).scalars().first()
    if not movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found.")

    if data.name is not None:
        movie.name = data.name
    if data.year is not None:
        movie.year = data.year
    if data.time is not None:
        movie.time = data.time
    if data.imdb is not None:
        movie.imdb = data.imdb
    if data.votes is not None:
        movie.votes = data.votes
    if data.meta_score is not None:
        movie.meta_score = data.meta_score
    if data.gross is not None:
        movie.gross = data.gross
    if data.description is not None:
        movie.description = data.description
    if data.price is not None:
        movie.price = data.price

    if data.certification is not None:
        cert = (
            await db.execute(
                select(CertificationModel).where(func.lower(CertificationModel.name) == data.certification.lower())
            )
        ).scalars().first()
        if not cert:
            cert = CertificationModel(name=data.certification)
            db.add(cert)
            await db.flush()
        movie.certification = cert

    # Replace relationship lists if provided
    if data.genres is not None:
        new_genres: list[GenreModel] = []
        for g in data.genres:
            if not g:
                continue
            genre = (
                await db.execute(select(GenreModel).where(func.lower(GenreModel.name) == g.lower()))
            ).scalars().first()
            if not genre:
                genre = GenreModel(name=g)
                db.add(genre)
                await db.flush()
            new_genres.append(genre)
        movie.genres = new_genres

    if data.directors is not None:
        new_directors: list[DirectorModel] = []
        for d in data.directors:
            if not d:
                continue
            director = (
                await db.execute(select(DirectorModel).where(func.lower(DirectorModel.name) == d.lower()))
            ).scalars().first()
            if not director:
                director = DirectorModel(name=d)
                db.add(director)
                await db.flush()
            new_directors.append(director)
        movie.directors = new_directors

    if data.stars is not None:
        new_stars: list[ActorModel] = []
        for s in data.stars:
            if not s:
                continue
            star = (
                await db.execute(select(ActorModel).where(func.lower(ActorModel.name) == s.lower()))
            ).scalars().first()
            if not star:
                star = ActorModel(name=s)
                db.add(star)
                await db.flush()
            new_stars.append(star)
        movie.actors = new_stars

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid movie update.")

    # return detail
    stmt = (
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            joinedload(MovieModel.genres),
            joinedload(MovieModel.directors),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.certification),
        )
    )
    movie = (await db.execute(stmt)).scalars().first()
    payload = MovieDetailSchema.model_validate(movie).model_dump()
    payload["stars"] = [{"id": a.id, "name": a.name} for a in getattr(movie, "actors", [])]
    return MovieDetailSchema(**payload)


@router.delete(
    "/movies/{movie_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete movie (Moderator/Admin)",
)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles(UserGroupEnum.MODERATOR, UserGroupEnum.ADMIN)),
):
    movie = (await db.execute(select(MovieModel).where(MovieModel.id == movie_id))).scalars().first()
    if not movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found.")

    try:
        await db.delete(movie)
        await db.commit()
    except IntegrityError:
        # E.g. movie has purchases (OrderItem ondelete=RESTRICT)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Movie cannot be deleted because it has purchases associated with it.",
        )

    return None
