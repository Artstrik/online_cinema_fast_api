from datetime import datetime
from typing import List, Optional, Dict, Any
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict

from src.database.models.payments import PaymentStatusEnum


class PaymentIntentCreateSchema(BaseModel):
    """Schema for creating a payment intent."""

    order_id: int = Field(..., gt=0, description="ID of the order to pay for")


class PaymentIntentResponseSchema(BaseModel):
    """Schema for payment intent response."""

    payment_id: int
    client_secret: str
    amount: Decimal
    currency: str = "usd"
    order_id: int


class PaymentWebhookSchema(BaseModel):
    """Schema for Stripe webhook payload."""

    type: str
    data: Dict[str, Any]


class PaymentItemSchema(BaseModel):
    """Schema for payment item."""

    id: int
    order_item_id: int
    price_at_payment: Decimal
    movie_name: str

    model_config = ConfigDict(from_attributes=True)


class PaymentDetailSchema(BaseModel):
    """Schema for detailed payment information."""

    id: int
    user_id: int
    order_id: int
    created_at: datetime
    status: PaymentStatusEnum
    amount: Decimal
    external_payment_id: Optional[str]
    items: List[PaymentItemSchema]

    model_config = ConfigDict(from_attributes=True)


class PaymentListItemSchema(BaseModel):
    """Schema for payment in list view."""

    id: int
    order_id: int
    created_at: datetime
    status: PaymentStatusEnum
    amount: Decimal

    model_config = ConfigDict(from_attributes=True)


class PaymentListResponseSchema(BaseModel):
    """Schema for list of payments."""

    payments: List[PaymentListItemSchema]
    total_payments: int
    page: int
    per_page: int


class PaymentRefundSchema(BaseModel):
    """Schema for payment refund request."""

    amount: Optional[Decimal] = Field(None, description="Amount to refund (if partial)")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for refund")


class PaymentRefundResponseSchema(BaseModel):
    """Schema for payment refund response."""

    message: str = "Payment refunded successfully"
    payment_id: int
    refund_amount: Decimal
    status: PaymentStatusEnum
