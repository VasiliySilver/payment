# Configure Stripe
import stripe
from decouple import config


stripe.api_key = config("STRIPE_SECRET_KEY")
webhook_secret = config("STRIPE_WEBHOOK_SECRET")
frontend_url = config("FRONTEND_URL")

# Price IDs from .env
price_ids = {
    "trial": config("TRIAL_PRICE_ID"),
    "monthly": config("MONTHLY_PRICE_ID"),
    "yearly": config("YEARLY_PRICE_ID"),
    "coach": config("COACH_PRICE_ID"),
    "assistant": config("ASSISTANT_PRICE_ID"),
}

# Basic validation for environment variables
if not stripe.api_key:
    raise ValueError("STRIPE_SECRET_KEY is not set in .env file")
if not webhook_secret:
    raise ValueError("STRIPE_WEBHOOK_SECRET is not set in .env file")
if not frontend_url:
    raise ValueError("FRONTEND_URL is not set in .env file")
if not all(price_ids.values()):
    missing = [k for k, v in price_ids.items() if not v]
    raise ValueError(f"Missing Price IDs in .env file: {', '.join(missing)}")

