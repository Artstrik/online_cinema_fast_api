"""
API routes for order operations.
"""
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.database.models import UserModel
from src.schemas.orders import (
    OrderResponseSchema,
    OrderCreateResponseSchema,
    OrderListResponseSchema,
    OrderListItemSchema,
    OrderCancelResponseSchema,
)
from src.services.order_service import OrderService
from src.security.http import get_current_active_user

router = APIRouter()


@router.post(
    "/",
    response_model=OrderCreateResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create order from cart",
    description="Create a new order from the user's shopping cart. Cart must not be empty. "
    "Validates that movies are available and not already purchased.",
)
async def create_order(
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> OrderCreateResponseSchema:
    """
    Create an order from the shopping cart.

    - Validates cart is not empty
    - Checks all movies are available
    - Ensures no movies are already purchased
    - Clears cart after order creation

    Returns the created order with all items.
    """
    order = await OrderService.create_order_from_cart(current_user.id, db)

    return OrderCreateResponseSchema(
        message="Order created successfully",
        order=OrderResponseSchema.model_validate(order),
    )


@router.get(
    "/",
    response_model=OrderListResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Get user's orders",
    description="Get a paginated list of the user's orders with filtering options.",
)
async def get_orders(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=50, description="Items per page"),
    status_filter: str
    | None = Query(None, description="Filter by status (pending, paid, canceled)"),
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> OrderListResponseSchema:
    """
    Get user's orders with pagination.

    - **page**: Page number (default: 1)
    - **per_page**: Items per page (default: 10, max: 50)
    - **status_filter**: Optional filter by order status

    Returns paginated list of orders.
    """
    orders, total_items = await OrderService.get_user_orders(
        user_id=current_user.id,
        db=db,
        page=page,
        per_page=per_page,
        status_filter=status_filter,
    )

    total_pages = (total_items + per_page - 1) // per_page

    # Convert to list items with count
    order_items = [
        OrderListItemSchema(
            id=order.id,
            created_at=order.created_at,
            status=order.status,
            total_amount=order.total_amount,
            items_count=len(order.items) if hasattr(order, "items") else 0,
        )
        for order in orders
    ]

    return OrderListResponseSchema(
        orders=order_items,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        total_items=total_items,
        prev_page=f"/orders/?page={page - 1}&per_page={per_page}" if page > 1 else None,
        next_page=f"/orders/?page={page + 1}&per_page={per_page}"
        if page < total_pages
        else None,
    )


@router.get(
    "/{order_id}/",
    response_model=OrderResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Get order details",
    description="Get detailed information about a specific order including all items.",
)
async def get_order(
    order_id: int,
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> OrderResponseSchema:
    """
    Get order details by ID.

    - **order_id**: Order ID

    Returns order with all items and movie details.
    Only accessible by the order owner.
    """
    order = await OrderService.get_order_by_id(order_id, current_user.id, db)

    return OrderResponseSchema.model_validate(order)


@router.patch(
    "/{order_id}/cancel/",
    response_model=OrderCancelResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Cancel order",
    description="Cancel a pending order. Orders can only be canceled if they are in PENDING status.",
)
async def cancel_order(
    order_id: int,
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> OrderCancelResponseSchema:
    """
    Cancel an order.

    - **order_id**: Order ID

    Only PENDING orders can be canceled.
    PAID orders require a refund request instead.
    """
    order = await OrderService.cancel_order(order_id, current_user.id, db)

    return OrderCancelResponseSchema(
        message="Order canceled successfully", order_id=order.id, status=order.status
    )
