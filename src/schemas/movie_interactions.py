"""
Pydantic schemas for Movie Interactions (Likes, Comments, Favorites, Ratings).
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator


class MovieLikeCreateSchema(BaseModel):
    """Schema for creating a like/dislike."""

    is_like: bool = Field(..., description="True for like, False for dislike")


class MovieLikeResponseSchema(BaseModel):
    """Schema for like response."""

    id: int
    user_id: int
    movie_id: int
    is_like: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MovieLikeStatsSchema(BaseModel):
    """Schema for movie like statistics."""

    movie_id: int
    likes_count: int
    dislikes_count: int
    user_like: Optional[bool] = None  # None if user hasn't liked, True/False otherwise


class MovieCommentCreateSchema(BaseModel):
    """Schema for creating a comment."""

    content: str = Field(
        ..., min_length=1, max_length=2000, description="Comment content"
    )
    parent_id: Optional[int] = Field(
        None, description="ID of parent comment for replies"
    )


class MovieCommentUpdateSchema(BaseModel):
    """Schema for updating a comment."""

    content: str = Field(
        ..., min_length=1, max_length=2000, description="Updated comment content"
    )


class MovieCommentUserSchema(BaseModel):
    """Schema for user info in comment."""

    id: int
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MovieCommentDetailSchema(BaseModel):
    """Schema for detailed comment information."""

    id: int
    user_id: int
    movie_id: int
    parent_id: Optional[int]
    content: str
    created_at: datetime
    updated_at: Optional[datetime]
    user: MovieCommentUserSchema
    replies: List["MovieCommentDetailSchema"] = []

    model_config = ConfigDict(from_attributes=True)


class MovieCommentListResponseSchema(BaseModel):
    """Schema for list of comments."""

    comments: List[MovieCommentDetailSchema]
    total_comments: int
    page: int
    per_page: int


class MovieFavoriteCreateSchema(BaseModel):
    """Schema for adding to favorites."""

    pass  # No additional data needed


class MovieFavoriteResponseSchema(BaseModel):
    """Schema for favorite response."""

    id: int
    user_id: int
    movie_id: int
    added_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MovieFavoriteDeleteResponseSchema(BaseModel):
    """Schema for favorite deletion response."""

    message: str = "Movie removed from favorites"
    movie_id: int


class MovieInFavoritesSchema(BaseModel):
    """Schema for movie in favorites list."""

    id: int
    uuid: str
    name: str
    year: int
    imdb: float
    price: float
    added_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MovieFavoritesListResponseSchema(BaseModel):
    """Schema for list of favorite movies."""

    favorites: List[MovieInFavoritesSchema]
    total_favorites: int
    page: int
    per_page: int


class MovieRatingCreateSchema(BaseModel):
    """Schema for creating/updating a rating."""

    rating: int = Field(..., ge=1, le=10, description="Rating from 1 to 10")

    @field_validator("rating")
    @classmethod
    def validate_rating_range(cls, v):
        if not 1 <= v <= 10:
            raise ValueError("Rating must be between 1 and 10")
        return v


class MovieRatingResponseSchema(BaseModel):
    """Schema for rating response."""

    id: int
    user_id: int
    movie_id: int
    rating: int
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class MovieRatingStatsSchema(BaseModel):
    """Schema for movie rating statistics."""

    movie_id: int
    average_rating: Optional[float] = None
    total_ratings: int
    user_rating: Optional[int] = None  # None if user hasn't rated
