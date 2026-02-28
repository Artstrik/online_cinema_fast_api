import datetime
from enum import Enum
from typing import Optional, TYPE_CHECKING

from sqlalchemy import ForeignKey, DateTime, DECIMAL, String, Enum as SQLAlchemyEnum
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.sql import func

from src.database.models.base import Base

if TYPE_CHECKING:
    from src.database.models.orders import OrderModel, OrderItemModel
    from src.database.models.accounts import UserModel


class PaymentStatusEnum(str, Enum):
    """Enumeration of possible payment statuses."""

    SUCCESSFUL = "successful"
    CANCELED = "canceled"
    REFUNDED = "refunded"
    PENDING = "pending"
    FAILED = "failed"


class PaymentModel(Base):
    """
    Model representing a payment transaction made by a user for an order.
    """

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    status: Mapped[PaymentStatusEnum] = mapped_column(
        SQLAlchemyEnum(PaymentStatusEnum),
        default=PaymentStatusEnum.PENDING,
        nullable=False,
    )
    amount: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    external_payment_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )

    # Relationships
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="payments")
    order: Mapped["OrderModel"] = relationship("OrderModel", back_populates="payments")
    items: Mapped[list["PaymentItemModel"]] = relationship(
        "PaymentItemModel", back_populates="payment", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<Payment(id={self.id}, user_id={self.user_id}, order_id={self.order_id}, "
            f"status='{self.status}', amount={self.amount})>"
        )


class PaymentItemModel(Base):
    """
    Model representing an individual item paid for in a single payment.
    Mirrors an order line item at the time of payment.
    """

    __tablename__ = "payment_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    payment_id: Mapped[int] = mapped_column(
        ForeignKey("payments.id", ondelete="CASCADE"), nullable=False
    )
    order_item_id: Mapped[int] = mapped_column(
        ForeignKey("order_items.id", ondelete="CASCADE"), nullable=False
    )
    price_at_payment: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)

    # Relationships
    payment: Mapped["PaymentModel"] = relationship(
        "PaymentModel", back_populates="items"
    )
    order_item: Mapped["OrderItemModel"] = relationship(
        "OrderItemModel", back_populates="payment_items"
    )

    def __repr__(self):
        return (
            f"<PaymentItem(id={self.id}, payment_id={self.payment_id}, "
            f"order_item_id={self.order_item_id}, price={self.price_at_payment})>"
        )
