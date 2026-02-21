"""
Stripe integration for payment processing.
"""
import stripe
from typing import Optional, Dict, Any
from decimal import Decimal

from src.config import get_settings


class StripeClient:
    """
    Client for interacting with Stripe API.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Stripe client.

        Args:
            api_key: Stripe secret API key. If not provided, uses settings.
        """
        settings = get_settings()
        self.api_key = api_key or settings.STRIPE_SECRET_KEY
        stripe.api_key = self.api_key

    async def create_payment_intent(
            self,
            amount: Decimal,
            currency: str = "usd",
            metadata: Optional[Dict[str, Any]] = None
    ) -> stripe.PaymentIntent:
        """
        Create a Stripe PaymentIntent.

        Args:
            amount: Amount in dollars (will be converted to cents)
            currency: Currency code (default: usd)
            metadata: Optional metadata to attach to the payment

        Returns:
            Stripe PaymentIntent object
        """
        # Convert dollars to cents
        amount_cents = int(amount * 100)

        payment_intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency=currency,
            metadata=metadata or {},
            automatic_payment_methods={
                'enabled': True,
            },
        )

        return payment_intent

    async def retrieve_payment_intent(
            self,
            payment_intent_id: str
    ) -> stripe.PaymentIntent:
        """
        Retrieve a PaymentIntent by ID.

        Args:
            payment_intent_id: Stripe PaymentIntent ID

        Returns:
            Stripe PaymentIntent object
        """
        return stripe.PaymentIntent.retrieve(payment_intent_id)

    async def confirm_payment_intent(
            self,
            payment_intent_id: str
    ) -> stripe.PaymentIntent:
        """
        Confirm a PaymentIntent.

        Args:
            payment_intent_id: Stripe PaymentIntent ID

        Returns:
            Confirmed Stripe PaymentIntent object
        """
        return stripe.PaymentIntent.confirm(payment_intent_id)

    async def cancel_payment_intent(
            self,
            payment_intent_id: str
    ) -> stripe.PaymentIntent:
        """
        Cancel a PaymentIntent.

        Args:
            payment_intent_id: Stripe PaymentIntent ID

        Returns:
            Canceled Stripe PaymentIntent object
        """
        return stripe.PaymentIntent.cancel(payment_intent_id)

    async def create_refund(
            self,
            payment_intent_id: str,
            amount: Optional[Decimal] = None,
            reason: Optional[str] = None
    ) -> stripe.Refund:
        """
        Create a refund for a payment.

        Args:
            payment_intent_id: Stripe PaymentIntent ID
            amount: Optional amount to refund in dollars (if None, full refund)
            reason: Optional reason for refund

        Returns:
            Stripe Refund object
        """
        refund_params = {
            'payment_intent': payment_intent_id,
        }

        if amount is not None:
            refund_params['amount'] = int(amount * 100)

        if reason:
            refund_params['reason'] = reason

        return stripe.Refund.create(**refund_params)

    def validate_webhook_signature(
            self,
            payload: str,
            sig_header: str,
            webhook_secret: Optional[str] = None
    ) -> stripe.Event:
        """
        Validate Stripe webhook signature and construct event.

        Args:
            payload: Raw request body
            sig_header: Stripe-Signature header value
            webhook_secret: Webhook secret. If not provided, uses settings.

        Returns:
            Constructed Stripe Event object

        Raises:
            stripe.error.SignatureVerificationError: If signature is invalid
        """
        settings = get_settings()
        secret = webhook_secret or settings.STRIPE_WEBHOOK_SECRET

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, secret
            )
            return event
        except ValueError:
            # Invalid payload
            raise ValueError("Invalid webhook payload")
        except stripe.error.SignatureVerificationError:
            # Invalid signature
            raise

    async def get_payment_method(
            self,
            payment_method_id: str
    ) -> stripe.PaymentMethod:
        """
        Retrieve a PaymentMethod by ID.

        Args:
            payment_method_id: Stripe PaymentMethod ID

        Returns:
            Stripe PaymentMethod object
        """
        return stripe.PaymentMethod.retrieve(payment_method_id)


# Singleton instance
_stripe_client: Optional[StripeClient] = None


def get_stripe_client() -> StripeClient:
    """
    Get or create Stripe client singleton.

    Returns:
        StripeClient instance
    """
    global _stripe_client
    if _stripe_client is None:
        _stripe_client = StripeClient()
    return _stripe_client
