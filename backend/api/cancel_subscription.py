from fastapi import HTTPException, logger, APIRouter
from pydantic import BaseModel
import stripe


router = APIRouter()


class CancelSubscriptionRequest(BaseModel):
    subscription_id: str

@router.post("/api/cancel-subscription")
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
