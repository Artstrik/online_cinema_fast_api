"""
Business logic for shopping cart operations.
"""
from typing import Optional, Tuple
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from fastapi import HTTPException, status

from src.database.models.cart import CartModel, CartItemModel
from src.database.models.movies import MovieModel
from src.database.models.orders import OrderItemModel


class CartService:
    """Service for managing shopping cart operations."""

    @staticmethod
    async def get_or_create_cart(user_id: int, db: AsyncSession) -> CartModel:
        """
        Get user's cart or create one if it doesn't exist.

        Args:
            user_id: User ID
            db: Database session

        Returns:
            User's cart
        """
        stmt = select(CartModel).where(CartModel.user_id == user_id)
        result = await db.execute(stmt)
        cart = result.scalars().first()

        if not cart:
            cart = CartModel(user_id=user_id)
            db.add(cart)
            await db.flush()

        return cart

    @staticmethod
    async def add_movie_to_cart(
        user_id: int, movie_id: int, db: AsyncSession
    ) -> CartItemModel:
        """
        Add a movie to user's cart with validation.

        Args:
            user_id: User ID
            movie_id: Movie ID to add
            db: Database session

        Returns:
            Created cart item

        Raises:
            HTTPException: If movie not found, already in cart, or already purchased
        """
        # Check if movie exists
        stmt = select(MovieModel).where(MovieModel.id == movie_id)
        result = await db.execute(stmt)
        movie = result.scalars().first()

        if not movie:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Movie with ID {movie_id} not found",
            )

        # Check if movie was already purchased by this user
        stmt = (
            select(OrderItemModel)
            .join(OrderItemModel.order)
            .where(
                OrderItemModel.movie_id == movie_id,
                OrderItemModel.order.has(user_id=user_id),
                OrderItemModel.order.has(status="paid"),
            )
        )
        result = await db.execute(stmt)
        if result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You have already purchased '{movie.name}'. Repeat purchases are not allowed.",
            )

        # Get or create cart
        cart = await CartService.get_or_create_cart(user_id, db)

        # Check if movie is already in cart
        stmt = select(CartItemModel).where(
            CartItemModel.cart_id == cart.id, CartItemModel.movie_id == movie_id
        )
        result = await db.execute(stmt)
        existing_item = result.scalars().first()

        if existing_item:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Movie '{movie.name}' is already in your cart",
            )

        # Add movie to cart
        cart_item = CartItemModel(cart_id=cart.id, movie_id=movie_id)
        db.add(cart_item)
        await db.commit()
        await db.refresh(cart_item)

        # Load movie relationship
        stmt = (
            select(CartItemModel)
            .options(joinedload(CartItemModel.movie))
            .where(CartItemModel.id == cart_item.id)
        )
        result = await db.execute(stmt)
        cart_item = result.scalars().first()

        return cart_item

    @staticmethod
    async def remove_movie_from_cart(
        user_id: int, movie_id: int, db: AsyncSession
    ) -> None:
        """
        Remove a movie from user's cart.

        Args:
            user_id: User ID
            movie_id: Movie ID to remove
            db: Database session

        Raises:
            HTTPException: If cart or item not found
        """
        # Get user's cart
        stmt = select(CartModel).where(CartModel.user_id == user_id)
        result = await db.execute(stmt)
        cart = result.scalars().first()

        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found"
            )

        # Find cart item
        stmt = select(CartItemModel).where(
            CartItemModel.cart_id == cart.id, CartItemModel.movie_id == movie_id
        )
        result = await db.execute(stmt)
        cart_item = result.scalars().first()

        if not cart_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found in cart"
            )

        await db.delete(cart_item)
        await db.commit()

    @staticmethod
    async def get_cart_with_items(
        user_id: int, db: AsyncSession
    ) -> Tuple[CartModel, int, Decimal]:
        """
        Get user's cart with items and calculate totals.

        Args:
            user_id: User ID
            db: Database session

        Returns:
            Tuple of (cart, items_count, total_price)
        """
        # Get cart with items and movies
        stmt = (
            select(CartModel)
            .options(joinedload(CartModel.items).joinedload(CartItemModel.movie))
            .where(CartModel.user_id == user_id)
        )
        result = await db.execute(stmt)
        cart = result.scalars().first()

        if not cart:
            # Create empty cart
            cart = CartModel(user_id=user_id)
            db.add(cart)
            await db.commit()
            await db.refresh(cart)
            return cart, 0, Decimal("0.00")

        items_count = len(cart.items)
        total_price = sum(Decimal(str(item.movie.price)) for item in cart.items)

        return cart, items_count, total_price

    @staticmethod
    async def clear_cart(user_id: int, db: AsyncSession) -> int:
        """
        Clear all items from user's cart.

        Args:
            user_id: User ID
            db: Database session

        Returns:
            Number of items removed
        """
        # Get user's cart
        stmt = select(CartModel).where(CartModel.user_id == user_id)
        result = await db.execute(stmt)
        cart = result.scalars().first()

        if not cart:
            return 0

        # Get items count before deletion
        stmt = select(CartItemModel).where(CartItemModel.cart_id == cart.id)
        result = await db.execute(stmt)
        items = result.scalars().all()
        items_count = len(items)

        # Delete all items
        for item in items:
            await db.delete(item)

        await db.commit()

        return items_count
