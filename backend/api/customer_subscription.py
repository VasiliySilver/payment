from fastapi import APIRouter, HTTPException, logger
import stripe


router = APIRouter()


@router.get("/api/subscription/{customer_id}")
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
