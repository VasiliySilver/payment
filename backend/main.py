import os
import stripe
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware # Import CORS Middleware
# Removed RedirectResponse as it's not used
from pydantic import BaseModel
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Configure Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
frontend_url = os.getenv("FRONTEND_URL")

# Price IDs from .env
price_ids = {
    "trial": os.getenv("TRIAL_PRICE_ID"),
    "monthly": os.getenv("MONTHLY_PRICE_ID"),
    "yearly": os.getenv("YEARLY_PRICE_ID"),
    "coach": os.getenv("COACH_PRICE_ID"),
    "assistant": os.getenv("ASSISTANT_PRICE_ID"),
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


app = FastAPI()

# --- CORS Configuration ---
# List of allowed origins (your frontend URL)
origins = [
    frontend_url, # Get from .env
    # You can add more origins here if needed, e.g., your production frontend URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Allows specified origins
    allow_credentials=True, # Allows cookies (not strictly needed here, but good practice)
    allow_methods=["*"], # Allows all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"], # Allows all headers
)
# --- End CORS Configuration ---

class CheckoutSessionRequest(BaseModel):
    product_type: str # 'trial', 'monthly', 'yearly', 'coach', 'assistant'

@app.post("/create-checkout-session")
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


@app.post("/webhook")
async def stripe_webhook(request: Request):
    """Handles incoming webhooks from Stripe."""
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    if not sig_header:
         logger.error("Missing Stripe-Signature header")
         raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        # Invalid payload
        logger.error(f"Invalid payload: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid payload: {e}")
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logger.error(f"Invalid signature: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid signature: {e}")
    except Exception as e:
        logger.error(f"Error constructing event: {e}")
        raise HTTPException(status_code=500, detail=f"Webhook error: {e}")

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        session_id = session.get('id')
        customer_id = session.get('customer')
        subscription_id = session.get('subscription') # Will be null for one-time payments
        payment_intent_id = session.get('payment_intent') # For one-time payments
        payment_status = session.get('payment_status')
        # You might want to retrieve the line items to know exactly what was purchased
        # line_items = stripe.checkout.Session.list_line_items(session_id, limit=5)
        # logger.info(f"Line items: {line_items}")

        logger.info(f"--- Webhook Event: checkout.session.completed ---")
        logger.info(f"  Session ID: {session_id}")
        logger.info(f"  Customer ID: {customer_id}")
        if subscription_id:
            logger.info(f"  Subscription ID: {subscription_id}")
        if payment_intent_id:
             logger.info(f"  Payment Intent ID: {payment_intent_id}")
        logger.info(f"  Payment Status: {payment_status}")
        logger.info(f"-------------------------------------------------")
        # In a real app:
        # - Verify the payment status ('paid').
        # - Store customer_id, subscription_id/payment_intent_id in your database, linking it to your user.
        # - Provision access based on the purchased product.

    # Handle payment_intent.succeeded for one-time payments (Upsells)
    # Note: checkout.session.completed often covers this, but handling both can be safer.
    elif event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        logger.info(f"--- Webhook Event: payment_intent.succeeded ---")
        logger.info(f"  Payment Intent ID: {payment_intent.get('id')}")
        logger.info(f"  Customer ID: {payment_intent.get('customer')}")
        logger.info(f"  Amount: {payment_intent.get('amount') / 100} {payment_intent.get('currency').upper()}") # Amount is in cents
        logger.info(f"-------------------------------------------------")
        # In a real app: Provision access for the one-time purchase.

    else:
        logger.info(f"Unhandled event type received: {event['type']}")

    return {"success": True}

@app.get("/api/subscription/{customer_id}")
async def get_subscription(customer_id: str):
    """Retrieves customer's subscription details."""
    try:
        subscriptions = stripe.Subscription.list(customer=customer_id, limit=1)
        if not subscriptions.data:
            return {"subscription": None}
        return {"subscription": subscriptions.data[0]}
    except Exception as e:
        logger.error(f"Error retrieving subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/payment-history/{customer_id}")
async def get_payment_history(customer_id: str):
    """Retrieves customer's payment history with detailed information."""
    try:
        # Get both payment intents and invoices for a complete history
        payment_intents = stripe.PaymentIntent.list(
            customer=customer_id,
            limit=100,
            expand=['data.latest_charge']
        )
        
        invoices = stripe.Invoice.list(
            customer=customer_id,
            limit=100,
            status='paid'
        )

        # Format payment history
        history = []
        
        # Process payment intents
        for intent in payment_intents.data:
            if intent.status == 'succeeded':
                history.append({
                    'id': intent.id,
                    'date': intent.created,
                    'amount': intent.amount / 100,  # Convert from cents
                    'currency': intent.currency.upper(),
                    'status': intent.status,
                    'description': intent.description or 'One-time payment',
                    'receipt_url': intent.latest_charge.receipt_url if intent.latest_charge else None
                })

        # Process invoices
        for invoice in invoices.data:
            history.append({
                'id': invoice.id,
                'date': invoice.created,
                'amount': invoice.amount_paid / 100,  # Convert from cents
                'currency': invoice.currency.upper(),
                'status': invoice.status,
                'description': invoice.description or f'Invoice {invoice.number}',
                'receipt_url': invoice.hosted_invoice_url,
                'pdf_url': invoice.invoice_pdf
            })

        # Sort by date descending
        history.sort(key=lambda x: x['date'], reverse=True)

        return {"payments": history}
    except Exception as e:
        logger.error(f"Error retrieving payment history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class CancelSubscriptionRequest(BaseModel):
    subscription_id: str

@app.post("/api/cancel-subscription")
async def cancel_subscription(request_data: CancelSubscriptionRequest):
    """Cancels a subscription by setting cancel_at_period_end to True."""
    try:
        logger.info(f"Attempting to cancel subscription: {request_data.subscription_id}")
        subscription = stripe.Subscription.modify(
            request_data.subscription_id,
            cancel_at_period_end=True
        )
        logger.info(f"Subscription {request_data.subscription_id} marked for cancellation at period end.")
        return {"status": "success", "subscription": subscription}
    except Exception as e:
        logger.error(f"Error canceling subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/checkout-session/{session_id}")
async def get_checkout_session(session_id: str):
    """Retrieves checkout session details, specifically the customer ID."""
    try:
        logger.info(f"Retrieving checkout session: {session_id}")
        session = stripe.checkout.Session.retrieve(session_id)
        customer_id = session.get('customer')
        if not customer_id:
             logger.warning(f"Customer ID not found in session: {session_id}")
             raise HTTPException(status_code=404, detail="Customer ID not found in this session.")
        
        logger.info(f"Found customer ID {customer_id} for session {session_id}")
        # Consider returning more details if needed by the frontend later
        return {"customer_id": customer_id} 
    except stripe.error.InvalidRequestError:
        logger.error(f"Invalid session ID: {session_id}")
        raise HTTPException(status_code=404, detail="Checkout session not found.")
    except Exception as e:
        logger.error(f"Error retrieving checkout session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def read_root():
    """Basic endpoint to check if the server is running."""
    return {"message": "Payment backend is running!"}


if __name__ == "__main__":
    logger.info("Starting FastAPI server...")
    # Use port 8000 by default, matching the Stripe CLI forward example
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
