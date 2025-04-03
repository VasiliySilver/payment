from fastapi import APIRouter, HTTPException, logger
import stripe


router = APIRouter()


@router.get("/api/payment-history/{customer_id}")
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
