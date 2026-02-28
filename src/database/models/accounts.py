import enum
from datetime import datetime, date, timedelta, timezone
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import (
    ForeignKey,
    String,
    Boolean,
    DateTime,
    Enum,
    Integer,
    func,
    Text,
    Date,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from src.database.models.base import Base
from src.database.validators import accounts as validators
from src.security.passwords import hash_password, verify_password
from src.security.utils import generate_secure_token

if TYPE_CHECKING:
    from src.database.models.cart import CartModel
    from src.database.models.orders import OrderModel
    from src.database.models.payments import PaymentModel
    from src.database.models.movies import (
        MovieLikeModel,
        MovieCommentModel,
        MovieFavoriteModel,
        MovieRatingModel,
    )


class UserGroupEnum(str, enum.Enum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


class GenderEnum(str, enum.Enum):
    MAN = "man"
    WOMAN = "woman"


class UserGroupModel(Base):
    __tablename__ = "user_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[UserGroupEnum] = mapped_column(
        Enum(UserGroupEnum), nullable=False, unique=True
    )

    users: Mapped[List["UserModel"]] = relationship("UserModel", back_populates="group")

    def __repr__(self):
        return f"<UserGroupModel(id={self.id}, name={self.name})>"


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    _hashed_password: Mapped[str] = mapped_column(
        "hashed_password", String(255), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    group_id: Mapped[int] = mapped_column(
        ForeignKey("user_groups.id", ondelete="CASCADE"), nullable=False
    )
    group: Mapped["UserGroupModel"] = relationship(
        "UserGroupModel", back_populates="users"
    )

    activation_token: Mapped[Optional["ActivationTokenModel"]] = relationship(
        "ActivationTokenModel", back_populates="user", cascade="all, delete-orphan"
    )

    password_reset_token: Mapped[Optional["PasswordResetTokenModel"]] = relationship(
        "PasswordResetTokenModel", back_populates="user", cascade="all, delete-orphan"
    )

    refresh_tokens: Mapped[List["RefreshTokenModel"]] = relationship(
        "RefreshTokenModel", back_populates="user", cascade="all, delete-orphan"
    )

    revoked_access_tokens: Mapped[List["RevokedAccessTokenModel"]] = relationship(
        "RevokedAccessTokenModel", back_populates="user", cascade="all, delete-orphan"
    )

    profile: Mapped[Optional["UserProfileModel"]] = relationship(
        "UserProfileModel", back_populates="user", cascade="all, delete-orphan"
    )

    # Shopping cart relationship
    cart: Mapped[Optional["CartModel"]] = relationship(
        "CartModel", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    # Orders relationship
    orders: Mapped[List["OrderModel"]] = relationship(
        "OrderModel", back_populates="user", cascade="all, delete-orphan"
    )

    # Payments relationship
    payments: Mapped[List["PaymentModel"]] = relationship(
        "PaymentModel", back_populates="user", cascade="all, delete-orphan"
    )

    # Movie interactions
    likes: Mapped[List["MovieLikeModel"]] = relationship(
        "MovieLikeModel", back_populates="user", cascade="all, delete-orphan"
    )
    comments: Mapped[List["MovieCommentModel"]] = relationship(
        "MovieCommentModel", back_populates="user", cascade="all, delete-orphan"
    )
    favorites: Mapped[List["MovieFavoriteModel"]] = relationship(
        "MovieFavoriteModel", back_populates="user", cascade="all, delete-orphan"
    )
    ratings: Mapped[List["MovieRatingModel"]] = relationship(
        "MovieRatingModel", back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def password(self) -> str:
        raise AttributeError("Password cannot be read directly")

    @password.setter
    def password(self, raw_password: str) -> None:
        self._hashed_password = hash_password(raw_password)

    def verify_password(self, raw_password: str) -> bool:
        return verify_password(raw_password, self._hashed_password)

    @validates("email")
    def validate_email(self, key, value):
        return validators.validate_email(value)

    def __repr__(self):
        return f"<UserModel(id={self.id}, email={self.email}, group={self.group_id})>"


class UserProfileModel(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    avatar: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    gender: Mapped[Optional[GenderEnum]] = mapped_column(Enum(GenderEnum), nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="profile")

    def __repr__(self):
        return f"<UserProfileModel(id={self.id}, user_id={self.user_id})>"


class TokenBaseModel(Base):
    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    @staticmethod
    def calculate_expiration(hours_valid: int) -> datetime:
        return datetime.now(timezone.utc) + timedelta(hours=hours_valid)


class ActivationTokenModel(TokenBaseModel):
    __tablename__ = "activation_tokens"

    user: Mapped[UserModel] = relationship("UserModel", back_populates="activation_token")
    token: Mapped[str] = mapped_column(
        String(512), unique=True, nullable=False, default=generate_secure_token
    )

    @classmethod
    def create(cls, user_id: int | Mapped[int], hours_valid: int = 24) -> "ActivationTokenModel":
        return cls(
            user_id=int(user_id),
            token=generate_secure_token(),
            expires_at=cls.calculate_expiration(hours_valid=hours_valid),
        )

    def __repr__(self):
        return f"<ActivationTokenModel(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"


class PasswordResetTokenModel(TokenBaseModel):
    __tablename__ = "password_reset_tokens"

    user: Mapped[UserModel] = relationship("UserModel", back_populates="password_reset_token")
    token: Mapped[str] = mapped_column(
        String(512), unique=True, nullable=False, default=generate_secure_token
    )

    @classmethod
    def create(cls, user_id: int | Mapped[int], hours_valid: int = 1) -> "PasswordResetTokenModel":
        return cls(
            user_id=int(user_id),
            token=generate_secure_token(),
            expires_at=cls.calculate_expiration(hours_valid=hours_valid),
        )

    def __repr__(self):
        return f"<PasswordResetTokenModel(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"


class RefreshTokenModel(TokenBaseModel):
    __tablename__ = "refresh_tokens"

    user: Mapped[UserModel] = relationship("UserModel", back_populates="refresh_tokens")
    token: Mapped[str] = mapped_column(
        String(512), unique=True, nullable=False, default=generate_secure_token
    )

    @classmethod
    def create(
        cls, user_id: int | Mapped[int], days_valid: int, token: str
    ) -> "RefreshTokenModel":
        expires_at = datetime.now(timezone.utc) + timedelta(days=days_valid)
        return cls(user_id=int(user_id), token=token, expires_at=expires_at)

    def __repr__(self):
        return f"<RefreshTokenModel(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"


class RevokedAccessTokenModel(Base):
    """
        Blacklisted (revoked) access tokens.
    """

    __tablename__ = "revoked_access_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    jti: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="revoked_access_tokens")

    def __repr__(self) -> str:
        return f"<RevokedAccessTokenModel(id={self.id}, user_id={self.user_id}, jti={self.jti})>"
