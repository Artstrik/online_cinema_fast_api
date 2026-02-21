"""
Pydantic schemas for Shopping Cart.
"""
from datetime import datetime
from typing import List, Optional
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict


class MovieInCartSchema(BaseModel):
    """Schema for movie information in cart."""
    id: int
    uuid: str
    name: str
    year: int
    time: int
    imdb: float
    price: Decimal
    description: str

    model_config = ConfigDict(from_attributes=True)


class CartItemSchema(BaseModel):
    """Schema for a single cart item."""
    id: int
    movie_id: int
    added_at: datetime
    movie: MovieInCartSchema

    model_config = ConfigDict(from_attributes=True)


class CartItemCreateSchema(BaseModel):
    """Schema for adding a movie to cart."""
    movie_id: int = Field(..., gt=0, description="ID of the movie to add to cart")


class CartResponseSchema(BaseModel):
    """Schema for cart response."""
    id: int
    user_id: int
    items: List[CartItemSchema]
    total_items: int
    total_price: Decimal

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_cart_model(cls, cart, items_count: int, total_price: Decimal):
        """Factory method to create response from cart model."""
        return cls(
            id=cart.id,
            user_id=cart.user_id,
            items=cart.items,
            total_items=items_count,
            total_price=total_price
        )


class CartClearResponseSchema(BaseModel):
    """Schema for cart clear response."""
    message: str = "Cart cleared successfully"
    items_removed: int


class CartItemDeleteResponseSchema(BaseModel):
    """Schema for cart item deletion response."""
    message: str = "Item removed from cart"
    movie_id: int
