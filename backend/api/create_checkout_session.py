
from fastapi import APIRouter, HTTPException, logger
from pydantic import BaseModel
import stripe

from config.settings import price_ids, frontend_url


router = APIRouter()

class CheckoutSessionRequest(BaseModel):
    product_type: str # 'trial', 'monthly', 'yearly', 'coach', 'assistant'

@router.post("/create-checkout-session")
async def create_checkout_session(request_data: CheckoutSessionRequest):
    """Creates a Stripe Checkout Session for the selected product type."""
    product_type = request_data.product_type
    price_id = price_ids.get(product_type)

    if not price_id:
        raise HTTPException(status_code=400, detail=f"Invalid product_type: {product_type}. Valid types are: {list(price_ids.keys())}")

    # Determine mode and success URL based on product type
    mode = 'subscription' # Default for monthly, yearly
    success_path = "/success" # Default success page

    if product_type == 'trial':
        success_path = "/subscription" # Next step after trial
        mode = 'payment' # Trial is likely a one-time payment to start
    elif product_type in ['monthly', 'yearly']:
        success_path = "/upsell/coach" # Next step after subscription
        mode = 'subscription' # These are actual subscriptions
    elif product_type == 'coach':
        success_path = "/upsell/assistant" # Next step after coach upsell
        mode = 'payment' # One-time payment
    elif product_type == 'assistant':
        success_path = "/funnel/complete" # Final step after assistant upsell
        mode = 'payment' # One-time payment

    # Construct URLs
    # We add product_type to success URL to potentially show context on success page
    # or help drive logic on the next step page.
    success_url = f"{frontend_url}{success_path}?session_id={{CHECKOUT_SESSION_ID}}&product={product_type}"
    cancel_url = f"{frontend_url}/cancel?product={product_type}" # Add context to cancel URL too

    try:
        # --- Add customer_creation for payment mode ---
        session_params = {
            'line_items': [{'price': price_id, 'quantity': 1}],
            'mode': mode,
            'success_url': success_url,
            'cancel_url': cancel_url,
        }
        if mode == 'payment':
            session_params['customer_creation'] = 'always'
            # Optional: You could also add 'customer_email': 'user@example.com' 
            # if you collect email before checkout to link payments better.
        # --- End customer_creation addition ---

        checkout_session = stripe.checkout.Session.create(**session_params)
        
        logger.info(f"Created checkout session ({product_type}): {checkout_session.id} with mode '{mode}'")
        return {"url": checkout_session.url}
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        raise HTTPException(status_code=500, detail=str(e))