"""
Business logic for payment operations.
"""
from typing import List, Optional, Dict, Any
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from fastapi import HTTPException, status

from src.database.models.payments import (
    PaymentModel,
    PaymentItemModel,
    PaymentStatusEnum,
)
from src.database.models.orders import (
    OrderModel,
    OrderItemModel,
    OrderStatusEnum
)

from src.integrations.stripe_client import get_stripe_client
from src.services.order_service import OrderService


class PaymentService:
    """Service for managing payment operations."""

    @staticmethod
    async def create_payment_intent(
            order_id: int,
            user_id: int,
            db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Create a Stripe payment intent for an order.

        Args:
            order_id: Order ID to pay for
            user_id: User ID
            db: Database session

        Returns:
            Dictionary with payment_id and client_secret

        Raises:
            HTTPException: If order not found, already paid, or validation fails
        """
        # Get order
        order = await OrderService.get_order_by_id(order_id, user_id, db)

        # Validate order status
        if order.status == OrderStatusEnum.PAID:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order is already paid"
            )

        if order.status == OrderStatusEnum.CANCELED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot pay for a canceled order"
            )

        # Check if payment already exists for this order
        stmt = select(PaymentModel).where(
            PaymentModel.order_id == order_id,
            PaymentModel.status.in_([PaymentStatusEnum.PENDING, PaymentStatusEnum.SUCCESSFUL])
        )
        result = await db.execute(stmt)
        existing_payment = result.scalars().first()

        if existing_payment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment already exists for this order (Payment ID: {existing_payment.id})"
            )

        # Revalidate total amount (in case prices changed)
        calculated_total = sum(
            Decimal(str(item.price_at_order)) for item in order.items
        )

        if calculated_total != order.total_amount:
            # Update order total
            order.total_amount = calculated_total
            await db.flush()

        # Create Stripe payment intent
        stripe_client = get_stripe_client()

        try:
            payment_intent = await stripe_client.create_payment_intent(
                amount=order.total_amount,
                currency="usd",
                metadata={
                    "order_id": order_id,
                    "user_id": user_id,
                }
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create payment intent: {str(e)}"
            )

        # Create payment record
        payment = PaymentModel(
            user_id=user_id,
            order_id=order_id,
            status=PaymentStatusEnum.PENDING,
            amount=order.total_amount,
            external_payment_id=payment_intent.id
        )
        db.add(payment)
        await db.flush()

        # Create payment items
        for order_item in order.items:
            payment_item = PaymentItemModel(
                payment_id=payment.id,
                order_item_id=order_item.id,
                price_at_payment=order_item.price_at_order
            )
            db.add(payment_item)

        await db.commit()
        await db.refresh(payment)

        return {
            "payment_id": payment.id,
            "client_secret": payment_intent.client_secret,
            "amount": float(order.total_amount),
            "currency": "usd",
            "order_id": order_id
        }

    @staticmethod
    async def process_webhook_event(
            event_type: str,
            event_data: Dict[str, Any],
            db: AsyncSession
    ) -> None:
        """
        Process Stripe webhook event.

        Args:
            event_type: Stripe event type
            event_data: Event data
            db: Database session
        """
        if event_type == "payment_intent.succeeded":
            await PaymentService._handle_payment_success(event_data, db)
        elif event_type == "payment_intent.payment_failed":
            await PaymentService._handle_payment_failure(event_data, db)
        elif event_type == "charge.refunded":
            await PaymentService._handle_refund(event_data, db)

    @staticmethod
    async def _handle_payment_success(
            event_data: Dict[str, Any],
            db: AsyncSession
    ) -> None:
        """Handle successful payment webhook."""
        payment_intent_id = event_data['object']['id']

        # Find payment
        stmt = select(PaymentModel).where(
            PaymentModel.external_payment_id == payment_intent_id
        )
        result = await db.execute(stmt)
        payment = result.scalars().first()

        if not payment:
            return  # Payment not found, might be from another system

        # Update payment status
        payment.status = PaymentStatusEnum.SUCCESSFUL

        # Update order status
        await OrderService.update_order_status(
            payment.order_id,
            OrderStatusEnum.PAID,
            db
        )

        await db.commit()

    @staticmethod
    async def _handle_payment_failure(
            event_data: Dict[str, Any],
            db: AsyncSession
    ) -> None:
        """Handle failed payment webhook."""
        payment_intent_id = event_data['object']['id']

        # Find payment
        stmt = select(PaymentModel).where(
            PaymentModel.external_payment_id == payment_intent_id
        )
        result = await db.execute(stmt)
        payment = result.scalars().first()

        if not payment:
            return

        payment.status = PaymentStatusEnum.FAILED
        await db.commit()

    @staticmethod
    async def _handle_refund(
            event_data: Dict[str, Any],
            db: AsyncSession
    ) -> None:
        """Handle refund webhook."""
        charge_id = event_data['object']['id']

        # Find payment by charge ID (might need to adjust based on Stripe data)
        # This is simplified - in production, you'd need proper charge tracking
        stmt = select(PaymentModel).where(
            PaymentModel.status == PaymentStatusEnum.SUCCESSFUL
        )
        result = await db.execute(stmt)
        payment = result.scalars().first()

        if payment:
            payment.status = PaymentStatusEnum.REFUNDED
            await db.commit()

    @staticmethod
    async def get_payment_history(
            user_id: int,
            db: AsyncSession,
            page: int = 1,
            per_page: int = 10
    ) -> tuple[List[PaymentModel], int]:
        """
        Get user's payment history.

        Args:
            user_id: User ID
            db: Database session
            page: Page number
            per_page: Items per page

        Returns:
            Tuple of (payments list, total count)
        """
        offset = (page - 1) * per_page

        # Get total count
        stmt = select(func.count(PaymentModel.id)).where(PaymentModel.user_id == user_id)
        result = await db.execute(stmt)
        total_count = result.scalar() or 0

        # Get payments
        stmt = (
            select(PaymentModel)
            .options(
                joinedload(PaymentModel.items).joinedload(PaymentItemModel.order_item)
            )
            .where(PaymentModel.user_id == user_id)
            .order_by(PaymentModel.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        result = await db.execute(stmt)
        payments = result.scalars().unique().all()

        return list(payments), total_count

    @staticmethod
    async def get_payment_by_id(
            payment_id: int,
            user_id: int,
            db: AsyncSession
    ) -> PaymentModel:
        """
        Get payment by ID with validation.

        Args:
            payment_id: Payment ID
            user_id: User ID
            db: Database session

        Returns:
            Payment with items

        Raises:
            HTTPException: If payment not found or access denied
        """
        stmt = (
            select(PaymentModel)
            .options(
                joinedload(PaymentModel.items)
                .joinedload(PaymentItemModel.order_item)
                .joinedload(OrderItemModel.movie)
            )
            .where(PaymentModel.id == payment_id)
        )
        result = await db.execute(stmt)
        payment = result.scalars().first()

        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment {payment_id} not found"
            )

        if payment.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this payment"
            )

        return payment

    @staticmethod
    async def refund_payment(
            payment_id: int,
            user_id: int,
            amount: Optional[Decimal],
            reason: Optional[str],
            db: AsyncSession
    ) -> PaymentModel:
        """
        Refund a payment.

        Args:
            payment_id: Payment ID
            user_id: User ID
            amount: Optional amount to refund
            reason: Refund reason
            db: Database session

        Returns:
            Updated payment

        Raises:
            HTTPException: If validation fails
        """
        payment = await PaymentService.get_payment_by_id(payment_id, user_id, db)

        if payment.status != PaymentStatusEnum.SUCCESSFUL:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only successful payments can be refunded"
            )

        # Process refund through Stripe
        stripe_client = get_stripe_client()

        try:
            await stripe_client.create_refund(
                payment_intent_id=payment.external_payment_id,
                amount=amount,
                reason=reason
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process refund: {str(e)}"
            )

        payment.status = PaymentStatusEnum.REFUNDED
        await db.commit()
        await db.refresh(payment)

        return payment
