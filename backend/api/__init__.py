from fastapi import FastAPI
from . import (
    cancel_subscription,
    checkout_session,
    create_checkout_session,
    customer_subscription,
    payment_history,
    read_root,
    stripe_webhook
)


def create_api_routes(app: FastAPI):
    """
    Create API routes for the application.

    Args:
        app: The FastAPI application instance.
    """
    app.include_router(
        cancel_subscription.router,
        tags=["Cancel Subscription"],
    )
    app.include_router(
        checkout_session.router,
        tags=["Checkout Session"],
    )
    app.include_router(
        create_checkout_session.router,
        tags=["Create Checkout Session"],
    )
    app.include_router(
        customer_subscription.router,
        tags=["Customer Subscription"],
    )
    app.include_router(
        payment_history.router,
        tags=["Payment History"],
    )
    app.include_router(
        read_root.router,
        tags=["Read Root"],
    )
    app.include_router(
        stripe_webhook.router,
        tags=["Stripe Webhook"],
    )
    