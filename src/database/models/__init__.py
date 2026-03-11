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
    RevokedAccessTokenModel
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
    MoviesGenresModel,
    ActorsMoviesModel,
    MoviesLanguagesModel,
    DirectorsMoviesModel,
)

from src.database.models.cart import (
    CartModel,
    CartItemModel,
)

from src.database.models.orders import (
    OrderModel,
    OrderItemModel,
    OrderStatusEnum,
)

from src.database.models.payments import (
    PaymentModel,
    PaymentItemModel,
    PaymentStatusEnum,
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
    "RevokedAccessTokenModel",
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
    "MoviesGenresModel",
    "ActorsMoviesModel",
    "MoviesLanguagesModel",
    "DirectorsMoviesModel",
    # Cart models
    "CartModel",
    "CartItemModel",
    # Order models
    "OrderModel",
    "OrderItemModel",
    "OrderStatusEnum",
    # Payment models
    "PaymentModel",
    "PaymentItemModel",
    "PaymentStatusEnum",
]
