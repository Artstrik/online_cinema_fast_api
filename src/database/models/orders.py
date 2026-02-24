"""
Order models for the Theater application.
"""
import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import ForeignKey, DateTime, DECIMAL, Enum as SQLAlchemyEnum
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.sql import func

from src.database.models.base import Base
from src.database.models.accounts import UserModel
from src.database.models.payments import PaymentModel
from src.database.models.movies import MovieModel
from src.database.models.payments import PaymentItemModel


class OrderStatusEnum(str, Enum):
    """Enumeration of possible order statuses."""

    PENDING = "pending"
    PAID = "paid"
    CANCELED = "canceled"


class OrderModel(Base):
    """
    Model representing a user's order.
    Contains one or more movies that the user intends to purchase.
    """

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    status: Mapped[OrderStatusEnum] = mapped_column(
        SQLAlchemyEnum(OrderStatusEnum), default=OrderStatusEnum.PENDING, nullable=False
    )
    total_amount: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2), nullable=True)

    # Relationships
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="orders")
    items: Mapped[list["OrderItemModel"]] = relationship(
        "OrderItemModel", back_populates="order", cascade="all, delete-orphan"
    )
    payments: Mapped[list["PaymentModel"]] = relationship(
        "PaymentModel", back_populates="order", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<Order(id={self.id}, user_id={self.user_id}, "
            f"status='{self.status}', total_amount={self.total_amount})>"
        )


class OrderItemModel(Base):
    """
    Model representing a single line item within an order.
    Links a specific movie to the order with price snapshot at order time.
    """

    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    movie_id: Mapped[int] = mapped_column(
        ForeignKey(
            "movies.id", ondelete="RESTRICT"
        ),  # Don't allow deletion of purchased movies
        nullable=False,
    )
    price_at_order: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)

    # Relationships
    order: Mapped["OrderModel"] = relationship("OrderModel", back_populates="items")
    movie: Mapped["MovieModel"] = relationship("MovieModel")
    payment_items: Mapped[list["PaymentItemModel"]] = relationship(
        "PaymentItemModel", back_populates="order_item"
    )

    def __repr__(self):
        return (
            f"<OrderItem(id={self.id}, order_id={self.order_id}, "
            f"movie_id={self.movie_id}, price={self.price_at_order})>"
        )
