from typing import Optional
from fastapi import APIRouter, Depends, status, Query, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.database.models import UserModel
from src.schemas.payments import (
    PaymentIntentResponseSchema,
    PaymentDetailSchema,
    PaymentListResponseSchema,
    PaymentListItemSchema,
    PaymentRefundResponseSchema,
    PaymentRefundSchema,
)
from src.services.payment_service import PaymentService
from src.security.http import get_current_active_user

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post(
    "/create-intent",
    response_model=PaymentIntentResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create payment intent",
    description="Create a Stripe payment intent for an order. "
                "Returns client secret for frontend payment confirmation."
)
async def create_payment_intent(
        order_id: int = Query(..., description="Order ID to pay for"),
        current_user: UserModel = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
) -> PaymentIntentResponseSchema:
    """
    Create a payment intent for an order.

    - **order_id**: Order ID to create payment for

    Returns payment ID and client secret for Stripe.js
    """
    result = await PaymentService.create_payment_intent(
        order_id=order_id,
        user_id=current_user.id,
        db=db
    )

    return PaymentIntentResponseSchema(**result)


@router.post(
    "/confirm",
    response_model=PaymentDetailSchema,
    status_code=status.HTTP_200_OK,
    summary="Confirm payment",
    description="Confirm payment after user completes payment in Stripe. "
                "Updates order status to PAID and sends confirmation email."
)
async def confirm_payment(
        payment_id: int = Query(..., description="Payment ID to confirm"),
        current_user: UserModel = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
) -> PaymentDetailSchema:
    """
    Confirm payment completion.

    - **payment_id**: Payment ID to confirm

    Updates order status and sends email confirmation.
    """
    payment = await PaymentService.confirm_payment(
        payment_id=payment_id,
        user_id=current_user.id,
        db=db
    )

    return PaymentDetailSchema.model_validate(payment)


@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
    summary="Stripe webhook",
    description="Handle webhooks from Stripe for payment status updates. "
                "This endpoint is called by Stripe, not by users."
)
async def stripe_webhook(
        request: Request,
        db: AsyncSession = Depends(get_db)
):
    """
    Handle Stripe webhook events.

    Automatically updates payment and order statuses based on Stripe events.
    Requires Stripe webhook signature validation.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    try:
        await PaymentService.handle_stripe_webhook(payload, sig_header, db)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/",
    response_model=PaymentListResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Get payment history",
    description="Get user's payment history with pagination and filtering."
)
async def get_payments(
        page: int = Query(1, ge=1, description="Page number"),
        per_page: int = Query(10, ge=1, le=50, description="Items per page"),
        status_filter: Optional[str] = Query(None, description="Filter by status"),
        current_user: UserModel = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
) -> PaymentListResponseSchema:
    """
    Get user's payment history.

    - **page**: Page number (default: 1)
    - **per_page**: Items per page (default: 10, max: 50)
    - **status_filter**: Optional filter by payment status

    Returns paginated list of payments.
    """
    payments, total_items = await PaymentService.get_user_payments(
        user_id=current_user.id,
        db=db,
        page=page,
        per_page=per_page,
        status_filter=status_filter
    )

    # Convert to list items
    payment_items = [
        PaymentListItemSchema.model_validate(payment)
        for payment in payments
    ]

    return PaymentListResponseSchema(
        payments=payment_items,
        total_payments=total_items,
        page=page,
        per_page=per_page
    )


@router.get(
    "/{payment_id}",
    response_model=PaymentDetailSchema,
    status_code=status.HTTP_200_OK,
    summary="Get payment details",
    description="Get detailed information about a specific payment."
)
async def get_payment(
        payment_id: int,
        current_user: UserModel = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
) -> PaymentDetailSchema:
    """
    Get payment details by ID.

    - **payment_id**: Payment ID

    Returns payment with all items.
    Only accessible by the payment owner.
    """
    payment = await PaymentService.get_payment_by_id(
        payment_id=payment_id,
        user_id=current_user.id,
        db=db
    )

    return PaymentDetailSchema.model_validate(payment)


@router.post(
    "/{payment_id}/refund",
    response_model=PaymentRefundResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Request refund",
    description="Request a refund for a successful payment. "
                "Creates a refund request that will be processed by admins."
)
async def request_refund(
        payment_id: int,
        refund_data: PaymentRefundSchema,
        current_user: UserModel = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
) -> PaymentRefundResponseSchema:
    """
    Request a payment refund.

    - **payment_id**: Payment ID
    - **refund_data**: Refund details (amount, reason)

    Only SUCCESSFUL payments can be refunded.
    """
    payment = await PaymentService.request_refund(
        payment_id=payment_id,
        user_id=current_user.id,
        amount=refund_data.amount,
        reason=refund_data.reason,
        db=db
    )

    return PaymentRefundResponseSchema(
        message="Refund requested successfully. It will be processed by our team.",
        payment_id=payment.id,
        refund_amount=refund_data.amount or payment.amount,
        status=payment.status
    )
