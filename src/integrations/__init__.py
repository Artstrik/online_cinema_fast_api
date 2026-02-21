"""
External integrations module.

Contains clients for third-party services like Stripe.
"""

from src.integrations.stripe_client import StripeClient, get_stripe_client

__all__ = [
    "StripeClient",
    "get_stripe_client",
]
