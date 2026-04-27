import os
import stripe

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")


def create_checkout_session(api_key: str, plan: str, amount: int, currency: str):
    if not stripe.api_key:
        raise RuntimeError("STRIPE_SECRET_KEY environment variable is not set.")

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        line_items=[
            {
                "price_data": {
                    "currency": currency.lower(),
                    "product_data": {
                        "name": f"CleanCore Validation API - {plan} Plan"
                    },
                    "unit_amount": amount * 100
                },
                "quantity": 1
            }
        ],
        metadata={
            "api_key": api_key,
            "plan": plan
        },
        success_url="http://clean-core-validation-api-production.up.railway.app/payment-success",
        cancel_url="http://clean-core-validation-api-production.up.railway.app/payment-cancelled"
    )

    return session.url


def verify_stripe_event(payload: bytes, sig_header: str):
    if not STRIPE_WEBHOOK_SECRET:
        raise RuntimeError("STRIPE_WEBHOOK_SECRET environment variable is not set.")

    event = stripe.Webhook.construct_event(
        payload,
        sig_header,
        STRIPE_WEBHOOK_SECRET
    )

    return event