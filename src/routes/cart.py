"""
API routes for shopping cart operations.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.database.models import UserModel
from src.schemas.cart import (
    CartItemCreateSchema,
    CartResponseSchema,
    CartClearResponseSchema,
    CartItemDeleteResponseSchema
)
from src.services.cart_service import CartService
from src.security.http import get_current_active_user

router = APIRouter()


@router.post(
    "/items/",
    response_model=CartResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Add movie to cart",
    description="Add a movie to the user's shopping cart. Validates that the movie exists "
                "and hasn't been purchased already."
)
async def add_movie_to_cart(
        item: CartItemCreateSchema,
        current_user: UserModel = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
) -> CartResponseSchema:
    """
    Add a movie to the shopping cart.

    - **movie_id**: ID of the movie to add

    Returns the updated cart with all items.
    """
    # Add movie to cart
    await CartService.add_movie_to_cart(current_user.id, item.movie_id, db)

    # Get updated cart
    cart, items_count, total_price = await CartService.get_cart_with_items(
        current_user.id, db
    )

    return CartResponseSchema.from_cart_model(cart, items_count, total_price)


@router.delete(
    "/items/{movie_id}/",
    response_model=CartItemDeleteResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Remove movie from cart",
    description="Remove a specific movie from the user's shopping cart."
)
async def remove_movie_from_cart(
        movie_id: int,
        current_user: UserModel = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
) -> CartItemDeleteResponseSchema:
    """
    Remove a movie from the shopping cart.

    - **movie_id**: ID of the movie to remove
    """
    await CartService.remove_movie_from_cart(current_user.id, movie_id, db)

    return CartItemDeleteResponseSchema(
        message="Item removed from cart",
        movie_id=movie_id
    )


@router.get(
    "/",
    response_model=CartResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Get shopping cart",
    description="Get the user's shopping cart with all items and total price."
)
async def get_cart(
        current_user: UserModel = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
) -> CartResponseSchema:
    """
    Get the user's shopping cart.

    Returns cart with all movies, item count, and total price.
    """
    cart, items_count, total_price = await CartService.get_cart_with_items(
        current_user.id, db
    )

    return CartResponseSchema.from_cart_model(cart, items_count, total_price)


@router.delete(
    "/",
    response_model=CartClearResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Clear shopping cart",
    description="Remove all items from the user's shopping cart."
)
async def clear_cart(
        current_user: UserModel = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
) -> CartClearResponseSchema:
    """
    Clear all items from the shopping cart.

    Returns the number of items removed.
    """
    items_removed = await CartService.clear_cart(current_user.id, db)

    return CartClearResponseSchema(
        message="Cart cleared successfully",
        items_removed=items_removed
    )
