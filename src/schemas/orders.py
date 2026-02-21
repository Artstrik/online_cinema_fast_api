"""
Pydantic schemas for Orders.
"""
from datetime import datetime
from typing import List, Optional
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict

from src.database.models.orders import OrderStatusEnum


class OrderItemSchema(BaseModel):
    """Schema for order item."""
    id: int
    movie_id: int
    movie_name: str
    price_at_order: Decimal

    model_config = ConfigDict(from_attributes=True)


class OrderResponseSchema(BaseModel):
    """Schema for order response (full order details)."""
    id: int
    user_id: int
    created_at: datetime
    status: OrderStatusEnum
    totaal_amount: Decimal
    items: List[OrderItemSchema]

    model_config = ConfigDict(from_attributes=True)


class OrderCreateSchema(BaseModel):
    """Schema for creating an order from cart."""
    message: str
    order: OrderResponseSchema

    model_config = ConfigDict(from_attributes=True)


class OrderCreateResponseSchema(BaseModel):
    """Schema for order creation response."""
    id: int
    user_id: int
    created_at: datetime
    status: OrderStatusEnum
    total_amount: Decimal
    items: List[OrderItemSchema]

    model_config = ConfigDict(from_attributes=True)


class OrderDetailSchema(BaseModel):
    """Schema for detailed order information."""
    id: int
    user_id: int
    created_at: datetime
    status: OrderStatusEnum
    total_amount: Decimal
    items: List[OrderItemSchema]

    model_config = ConfigDict(from_attributes=True)


class OrderListItemSchema(BaseModel):
    """Schema for order in list view."""
    id: int
    created_at: datetime
    status: OrderStatusEnum
    total_amount: Decimal
    items_count: int

    model_config = ConfigDict(from_attributes=True)


class OrderListResponseSchema(BaseModel):
    """Schema for list of orders."""
    orders: List[OrderListItemSchema]
    total_items: int
    page: int
    per_page: int


class OrderCancelSchema(BaseModel):
    """Schema for order cancellation."""
    reason: Optional[str] = Field(None, max_length=500, description="Reason for cancellation")


class OrderCancelResponseSchema(BaseModel):
    """Schema for order cancellation response."""
    message: str = "Order canceled successfully"
    order_id: int
    status: OrderStatusEnum


class OrderStatusUpdateSchema(BaseModel):
    """Schema for updating order status (admin only)."""
    status: OrderStatusEnum = Field(..., description="New order status")
