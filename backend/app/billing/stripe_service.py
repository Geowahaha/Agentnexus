from decimal import Decimal

import stripe

from app.core.config import settings


class StripeNotConfiguredError(RuntimeError):
    pass


class StripeService:
    def __init__(self) -> None:
        if not settings.stripe_secret_key:
            raise StripeNotConfiguredError("STRIPE_SECRET_KEY is not configured")
        stripe.api_key = settings.stripe_secret_key

    @staticmethod
    def is_configured() -> bool:
        return bool(settings.stripe_secret_key)

    def create_checkout_session(
        self,
        *,
        user_id: str,
        amount_usd: Decimal,
        customer_email: str | None = None,
    ) -> stripe.checkout.Session:
        amount_cents = int((amount_usd * 100).to_integral_value())
        params: dict = {
            "mode": "payment",
            "success_url": settings.stripe_success_url,
            "cancel_url": settings.stripe_cancel_url,
            "line_items": [
                {
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": amount_cents,
                        "product_data": {
                            "name": "AgentNexus Credits",
                            "description": f"Add ${amount_usd:.2f} to your AgentNexus wallet",
                        },
                    },
                    "quantity": 1,
                }
            ],
            "metadata": {
                "user_id": user_id,
                "amount_usd": str(amount_usd),
            },
        }
        if customer_email:
            params["customer_email"] = customer_email
        return stripe.checkout.Session.create(**params)

    def construct_webhook_event(self, payload: bytes, signature: str | None):
        if not settings.stripe_webhook_secret:
            raise StripeNotConfiguredError("STRIPE_WEBHOOK_SECRET is not configured")
        return stripe.Webhook.construct_event(payload, signature, settings.stripe_webhook_secret)