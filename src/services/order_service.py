"""
Business logic for order operations.
"""
from typing import List, Optional
from decimal import Decimal
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from fastapi import HTTPException, status

from src.database.models.orders import (
    OrderModel,
    OrderItemModel,
    OrderStatusEnum,
)
from src.database.models.cart import CartModel, CartItemModel
from src.database.models.movies import MovieModel


class OrderService:
    """Service for managing order operations."""

    @staticmethod
    async def create_order_from_cart(user_id: int, db: AsyncSession) -> OrderModel:
        """
        Create an order from user's cart.

        Validates:
        - Cart is not empty
        - All movies are available
        - No movies are already purchased
        - No pending orders with same movies

        Args:
            user_id: User ID
            db: Database session

        Returns:
            Created order

        Raises:
            HTTPException: If validation fails
        """
        # Get cart with items
        stmt = (
            select(CartModel)
            .options(joinedload(CartModel.items).joinedload(CartItemModel.movie))
            .where(CartModel.user_id == user_id)
        )
        result = await db.execute(stmt)
        cart = result.scalars().first()

        if not cart or not cart.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cart is empty. Add movies before creating an order.",
            )

        # Validate all movies are available
        unavailable_movies = []
        for item in cart.items:
            if not item.movie:
                unavailable_movies.append(item.movie_id)

        if unavailable_movies:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Some movies are no longer available: {unavailable_movies}",
            )

        # Check for already purchased movies
        movie_ids = [item.movie_id for item in cart.items]
        stmt = (
            select(OrderItemModel.movie_id)
            .join(OrderItemModel.order)
            .where(
                OrderItemModel.movie_id.in_(movie_ids),
                OrderItemModel.order.has(user_id=user_id),
                OrderItemModel.order.has(status=OrderStatusEnum.PAID),
            )
        )
        result = await db.execute(stmt)
        already_purchased = result.scalars().all()

        if already_purchased:
            # Get movie names
            stmt = select(MovieModel.name).where(MovieModel.id.in_(already_purchased))
            result = await db.execute(stmt)
            movie_names = result.scalars().all()

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You have already purchased: {', '.join(movie_names)}. "
                f"Please remove them from cart.",
            )

        # Calculate total amount
        total_amount = sum(Decimal(str(item.movie.price)) for item in cart.items)

        # Create order
        order = OrderModel(
            user_id=user_id, status=OrderStatusEnum.PENDING, total_amount=total_amount
        )
        db.add(order)
        await db.flush()

        # Create order items
        for cart_item in cart.items:
            order_item = OrderItemModel(
                order_id=order.id,
                movie_id=cart_item.movie_id,
                price_at_order=cart_item.movie.price,
            )
            db.add(order_item)

        # Clear cart
        for cart_item in cart.items:
            await db.delete(cart_item)

        await db.commit()
        await db.refresh(order)

        # Load relationships
        stmt = (
            select(OrderModel)
            .options(joinedload(OrderModel.items).joinedload(OrderItemModel.movie))
            .where(OrderModel.id == order.id)
        )
        result = await db.execute(stmt)
        order = result.scalars().first()

        return order

    @staticmethod
    async def get_order_by_id(
        order_id: int, user_id: int, db: AsyncSession
    ) -> OrderModel:
        """
        Get order by ID with validation.

        Args:
            order_id: Order ID
            user_id: User ID (for ownership validation)
            db: Database session

        Returns:
            Order with items

        Raises:
            HTTPException: If order not found or access denied
        """
        stmt = (
            select(OrderModel)
            .options(joinedload(OrderModel.items).joinedload(OrderItemModel.movie))
            .where(OrderModel.id == order_id)
        )
        result = await db.execute(stmt)
        order = result.scalars().first()

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {order_id} not found",
            )

        if order.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this order",
            )

        return order

    @staticmethod
    async def get_user_orders(
        user_id: int, db: AsyncSession, page: int = 1, per_page: int = 10
    ) -> tuple[List[OrderModel], int]:
        """
        Get user's orders with pagination.

        Args:
            user_id: User ID
            db: Database session
            page: Page number (1-based)
            per_page: Items per page

        Returns:
            Tuple of (orders list, total count)
        """
        offset = (page - 1) * per_page

        # Get total count
        stmt = select(func.count(OrderModel.id)).where(OrderModel.user_id == user_id)
        result = await db.execute(stmt)
        total_count = result.scalar() or 0

        # Get orders
        stmt = (
            select(OrderModel)
            .options(joinedload(OrderModel.items).joinedload(OrderItemModel.movie))
            .where(OrderModel.user_id == user_id)
            .order_by(OrderModel.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        result = await db.execute(stmt)
        orders = result.scalars().unique().all()

        return list(orders), total_count

    @staticmethod
    async def cancel_order(
        order_id: int, user_id: int, db: AsyncSession, reason: Optional[str] = None
    ) -> OrderModel:
        """
        Cancel an order (only if not paid).

        Args:
            order_id: Order ID
            user_id: User ID
            db: Database session
            reason: Optional cancellation reason

        Returns:
            Canceled order

        Raises:
            HTTPException: If order not found, already paid, or access denied
        """
        order = await OrderService.get_order_by_id(order_id, user_id, db)

        if order.status == OrderStatusEnum.PAID:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel a paid order. Please request a refund instead.",
            )

        if order.status == OrderStatusEnum.CANCELED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order is already canceled",
            )

        order.status = OrderStatusEnum.CANCELED
        await db.commit()
        await db.refresh(order)

        return order

    @staticmethod
    async def update_order_status(
        order_id: int, new_status: OrderStatusEnum, db: AsyncSession
    ) -> OrderModel:
        """
        Update order status (internal method for payment processing).

        Args:
            order_id: Order ID
            new_status: New status
            db: Database session

        Returns:
            Updated order
        """
        stmt = select(OrderModel).where(OrderModel.id == order_id)
        result = await db.execute(stmt)
        order = result.scalars().first()

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {order_id} not found",
            )

        order.status = new_status
        await db.commit()
        await db.refresh(order)

        return order
