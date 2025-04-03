from fastapi import APIRouter, HTTPException, Request, logger
import stripe

from config.settings import webhook_secret


router = APIRouter()


@router.post("/webhook")
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

