import datetime
import uuid as uuid_pkg
from enum import Enum
from typing import Optional

from sqlalchemy import (
    String, Float, Text, DECIMAL, UniqueConstraint, Date, ForeignKey,
    Table, Column, Integer, Boolean, DateTime, CheckConstraint, UUID
)
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.sql import func

from src.database.models.base import Base


class MovieStatusEnum(str, Enum):
    RELEASED = "Released"
    POST_PRODUCTION = "Post Production"
    IN_PRODUCTION = "In Production"


# Association tables for many-to-many relationships
MoviesGenresModel = Table(
    "movies_genres",
    Base.metadata,
    Column(
        "movie_id",
        ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True, nullable=False),
    Column(
        "genre_id",
        ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True, nullable=False),
)

ActorsMoviesModel = Table(
    "actors_movies",
    Base.metadata,
    Column(
        "movie_id",
        ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True, nullable=False),
    Column(
        "actor_id",
        ForeignKey("actors.id", ondelete="CASCADE"), primary_key=True, nullable=False),
)

MoviesLanguagesModel = Table(
    "movies_languages",
    Base.metadata,
    Column("movie_id", ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
    Column("language_id", ForeignKey("languages.id", ondelete="CASCADE"), primary_key=True),
)

DirectorsMoviesModel = Table(
    "directors_movies",
    Base.metadata,
    Column(
        "movie_id",
        ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True, nullable=False),
    Column(
        "director_id",
        ForeignKey("directors.id", ondelete="CASCADE"), primary_key=True, nullable=False),
)


class GenreModel(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    movies: Mapped[list["MovieModel"]] = relationship(
        "MovieModel",
        secondary=MoviesGenresModel,
        back_populates="genres"
    )

    def __repr__(self):
        return f"<Genre(name='{self.name}')>"


class ActorModel(Base):
    __tablename__ = "actors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    movies: Mapped[list["MovieModel"]] = relationship(
        "MovieModel",
        secondary=ActorsMoviesModel,
        back_populates="actors"
    )

    def __repr__(self):
        return f"<Actor(name='{self.name}')>"


class DirectorModel(Base):
    """Model representing a movie director."""
    __tablename__ = "directors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    movies: Mapped[list["MovieModel"]] = relationship(
        "MovieModel",
        secondary=DirectorsMoviesModel,
        back_populates="directors"
    )

    def __repr__(self):
        return f"<Director(name='{self.name}')>"


class CertificationModel(Base):
    """Model representing movie certifications (e.g., PG-13, R, etc.)."""
    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    movies: Mapped[list["MovieModel"]] = relationship("MovieModel", back_populates="certification")

    def __repr__(self):
        return f"<Certification(name='{self.name}')>"


class CountryModel(Base):
    __tablename__ = "countries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(3), unique=True, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    movies: Mapped[list["MovieModel"]] = relationship("MovieModel", back_populates="country")

    def __repr__(self):
        return f"<Country(code='{self.code}', name='{self.name}')>"


class LanguageModel(Base):
    __tablename__ = "languages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    movies: Mapped[list["MovieModel"]] = relationship(
        "MovieModel",
        secondary=MoviesLanguagesModel,
        back_populates="languages"
    )

    def __repr__(self):
        return f"<Language(name='{self.name}')>"


class MovieModel(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[uuid_pkg.UUID] = mapped_column(UUID(as_uuid=True), default=uuid_pkg.uuid4, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)  # Release year
    time: Mapped[int] = mapped_column(Integer, nullable=False)  # Duration in minutes
    imdb: Mapped[float] = mapped_column(Float, nullable=False)  # IMDb rating
    votes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # Number of votes
    meta_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Metascore
    gross: Mapped[Optional[float]] = mapped_column(DECIMAL(15, 2), nullable=True)  # Gross revenue
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False, default=0.00)

    # Legacy fields (keeping for backward compatibility)
    date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    overview: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[Optional[MovieStatusEnum]] = mapped_column(
        SQLAlchemyEnum(MovieStatusEnum), nullable=True
    )
    budget: Mapped[Optional[float]] = mapped_column(DECIMAL(15, 2), nullable=True)
    revenue: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Foreign keys
    certification_id: Mapped[Optional[int]] = mapped_column(ForeignKey("certifications.id"), nullable=True)
    country_id: Mapped[Optional[int]] = mapped_column(ForeignKey("countries.id"), nullable=True)

    # Relationships
    certification: Mapped[Optional["CertificationModel"]] = relationship(
        "CertificationModel", back_populates="movies"
    )
    country: Mapped[Optional["CountryModel"]] = relationship("CountryModel", back_populates="movies")

    genres: Mapped[list["GenreModel"]] = relationship(
        "GenreModel",
        secondary=MoviesGenresModel,
        back_populates="movies"
    )

    actors: Mapped[list["ActorModel"]] = relationship(
        "ActorModel",
        secondary=ActorsMoviesModel,
        back_populates="movies"
    )

    directors: Mapped[list["DirectorModel"]] = relationship(
        "DirectorModel",
        secondary=DirectorsMoviesModel,
        back_populates="movies"
    )

    languages: Mapped[list["LanguageModel"]] = relationship(
        "LanguageModel",
        secondary=MoviesLanguagesModel,
        back_populates="movies"
    )

    # New relationships for user interactions
    likes: Mapped[list["MovieLikeModel"]] = relationship(
        "MovieLikeModel", back_populates="movie", cascade="all, delete-orphan"
    )
    comments: Mapped[list["MovieCommentModel"]] = relationship(
        "MovieCommentModel", back_populates="movie", cascade="all, delete-orphan"
    )
    favorites: Mapped[list["MovieFavoriteModel"]] = relationship(
        "MovieFavoriteModel", back_populates="movie", cascade="all, delete-orphan"
    )
    ratings: Mapped[list["MovieRatingModel"]] = relationship(
        "MovieRatingModel", back_populates="movie", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("name", "year", "time", name="unique_movie_constraint"),
    )

    @classmethod
    def default_order_by(cls):
        return [cls.id.desc()]

    def __repr__(self):
        return f"<Movie(name='{self.name}', year={self.year}, imdb={self.imdb})>"


class MovieLikeModel(Base):
    """Model for user likes/dislikes on movies."""
    __tablename__ = "movie_likes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    is_like: Mapped[bool] = mapped_column(Boolean, nullable=False)  # True=like, False=dislike
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    movie: Mapped["MovieModel"] = relationship("MovieModel", back_populates="likes")
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="movie_likes")

    __table_args__ = (
        UniqueConstraint('user_id', 'movie_id', name='unique_user_movie_like'),
    )

    def __repr__(self):
        like_type = "like" if self.is_like else "dislike"
        return f"<MovieLike(user_id={self.user_id}, movie_id={self.movie_id}, type='{like_type}')>"


class MovieCommentModel(Base):
    """Model for user comments on movies."""
    __tablename__ = "movie_comments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("movie_comments.id", ondelete="CASCADE"), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # Relationships
    movie: Mapped["MovieModel"] = relationship("MovieModel", back_populates="comments")
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="movie_comments")
    parent: Mapped[Optional["MovieCommentModel"]] = relationship(
        "MovieCommentModel", remote_side=[id], backref="replies"
    )

    def __repr__(self):
        return f"<MovieComment(id={self.id}, user_id={self.user_id}, movie_id={self.movie_id})>"


class MovieFavoriteModel(Base):
    """Model for user's favorite movies."""
    __tablename__ = "movie_favorites"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    added_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    movie: Mapped["MovieModel"] = relationship("MovieModel", back_populates="favorites")
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="favorite_movies")

    __table_args__ = (
        UniqueConstraint('user_id', 'movie_id', name='unique_user_movie_favorite'),
    )

    def __repr__(self):
        return f"<MovieFavorite(user_id={self.user_id}, movie_id={self.movie_id})>"


class MovieRatingModel(Base):
    """Model for user ratings of movies (1-10 scale)."""
    __tablename__ = "movie_ratings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # Relationships
    movie: Mapped["MovieModel"] = relationship("MovieModel", back_populates="ratings")
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="movie_ratings")

    __table_args__ = (
        UniqueConstraint('user_id', 'movie_id', name='unique_user_movie_rating'),
        CheckConstraint('rating >= 1 AND rating <= 10', name='check_rating_range'),
    )

    def __repr__(self):
        return f"<MovieRating(user_id={self.user_id}, movie_id={self.movie_id}, rating={self.rating})>"
