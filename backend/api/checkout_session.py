from fastapi import APIRouter, HTTPException, logger
import stripe


router = APIRouter()

@router.get("/api/checkout-session/{session_id}")
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
