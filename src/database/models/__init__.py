"""
Database models for the Theater application.

This module exports all database models for easy import.
"""

from src.database.models.accounts import (
    UserModel,
    UserGroupModel,
    UserProfileModel,
    ActivationTokenModel,
    PasswordResetTokenModel,
    RefreshTokenModel,
    UserGroupEnum,
    GenderEnum,
)

from src.database.models.movies import (
    MovieModel,
    GenreModel,
    ActorModel,
    DirectorModel,
    CertificationModel,
    CountryModel,
    LanguageModel,
    MovieLikeModel,
    MovieCommentModel,
    MovieFavoriteModel,
    MovieRatingModel,
    MovieStatusEnum,
)

__all__ = [
    # Account models
    "UserModel",
    "UserGroupModel",
    "UserProfileModel",
    "ActivationTokenModel",
    "PasswordResetTokenModel",
    "RefreshTokenModel",
    "UserGroupEnum",
    "GenderEnum",
    # Movie models
    "MovieModel",
    "GenreModel",
    "ActorModel",
    "DirectorModel",
    "CertificationModel",
    "CountryModel",
    "LanguageModel",
    "MovieLikeModel",
    "MovieCommentModel",
    "MovieFavoriteModel",
    "MovieRatingModel",
    "MovieStatusEnum",

]
