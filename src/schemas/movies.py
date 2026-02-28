"""Movie schemas aligned with the project Technical Specification (TZ).

TZ highlights covered here:
- Movie core fields: uuid, name, year, time, imdb, votes, meta_score, gross, description, price
- Relations: certification (1-n), genres (m2m), directors (m2m), stars (m2m)
- List endpoints: pagination + filtering/sorting/search are implemented at route level.

Notes:
- Project DB model currently uses ActorModel for the "stars" entity.
  API schemas expose it as "stars" to match TZ wording.
"""

from __future__ import annotations

from decimal import Decimal
from typing import List, Optional, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


SortByMovies = Literal["year", "imdb", "votes", "price", "name"]
SortOrder = Literal["asc", "desc"]


class GenreSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class DirectorSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class StarSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class CertificationSchema(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    model_config = {"from_attributes": True}


class MovieListItemSchema(BaseModel):
    id: int
    uuid: UUID
    name: str
    year: int
    time: int
    imdb: float
    votes: int
    price: Decimal

    model_config = {"from_attributes": True}


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieDetailSchema(BaseModel):
    id: int
    uuid: UUID
    name: str
    year: int
    time: int
    imdb: float
    votes: int
    meta_score: Optional[float] = None
    gross: Optional[Decimal] = None
    description: str
    price: Decimal

    certification: Optional[CertificationSchema] = None
    genres: List[GenreSchema] = []
    directors: List[DirectorSchema] = []
    stars: List[StarSchema] = []

    model_config = {"from_attributes": True}


class MovieCreateSchema(BaseModel):
    name: str = Field(..., max_length=255)
    year: int = Field(..., ge=1888, le=2200)
    time: int = Field(..., ge=1, le=1000, description="Duration in minutes")
    imdb: float = Field(..., ge=0, le=10)
    votes: int = Field(..., ge=0)
    meta_score: Optional[float] = Field(None, ge=0, le=100)
    gross: Optional[Decimal] = Field(None, ge=0)
    description: str = Field(..., min_length=10)
    price: Decimal = Field(..., ge=0)

    certification: str = Field(..., description="Certification name, e.g. PG-13")
    genres: List[str] = Field(default_factory=list)
    directors: List[str] = Field(default_factory=list)
    stars: List[str] = Field(default_factory=list)

    @field_validator("certification")
    @classmethod
    def normalize_certification(cls, v: str) -> str:
        return v.strip()

    @field_validator("genres", "directors", "stars", mode="before")
    @classmethod
    def normalize_names(cls, v):
        if v is None:
            return []
        return [str(item).strip() for item in v]


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    year: Optional[int] = Field(None, ge=1888, le=2200)
    time: Optional[int] = Field(None, ge=1, le=1000)
    imdb: Optional[float] = Field(None, ge=0, le=10)
    votes: Optional[int] = Field(None, ge=0)
    meta_score: Optional[float] = Field(None, ge=0, le=100)
    gross: Optional[Decimal] = Field(None, ge=0)
    description: Optional[str] = Field(None, min_length=10)
    price: Optional[Decimal] = Field(None, ge=0)

    certification: Optional[str] = None
    genres: Optional[List[str]] = None
    directors: Optional[List[str]] = None
    stars: Optional[List[str]] = None

    @field_validator("certification")
    @classmethod
    def normalize_certification(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return v.strip()

    @field_validator("genres", "directors", "stars", mode="before")
    @classmethod
    def normalize_names(cls, v):
        if v is None:
            return v
        return [str(item).strip() for item in v]


class GenreWithCountSchema(BaseModel):
    id: int
    name: str
    movies_count: int


class GenreListWithCountResponseSchema(BaseModel):
    genres: List[GenreWithCountSchema]
