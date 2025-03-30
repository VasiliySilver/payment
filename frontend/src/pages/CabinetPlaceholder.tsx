import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

// --- Interfaces ---
interface PaymentHistoryItem {
    id: string;
    date: number | string; // Stripe uses timestamps (number) or ISO strings
    amount: number;
    currency: string;
    status: string;
    description: string;
    receiptUrl?: string | null; // Optional receipt URL
    pdfUrl?: string | null; // Optional invoice PDF URL
}

interface Subscription {
    id: string;
    status: string;
    plan: string;
    currentPeriodEnd: number | string; // Stripe uses timestamps (number)
    cancel_at_period_end: boolean; // Indicates if cancellation is scheduled
}

// --- Helper Functions ---
const formatDate = (timestamp: number | string): string => {
    // Stripe often returns timestamps in seconds, multiply by 1000 for JS Date
    const dateValue = typeof timestamp === 'string' ? Date.parse(timestamp) : timestamp * 1000;
    if (isNaN(dateValue)) {
        return 'Invalid Date';
    }
    // Use locale-specific date format
    return new Date(dateValue).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' });
};

const formatCurrency = (amount: number, currency: string = 'usd'): string => {
    // Use locale-specific currency format
    return new Intl.NumberFormat(undefined, { style: 'currency', currency: currency.toUpperCase() }).format(amount);
};
// --- End Helper Functions ---


const CabinetPlaceholder: React.FC = () => {
    const [subscription, setSubscription] = useState<Subscription | null>(null);
    const [payments, setPayments] = useState<PaymentHistoryItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null); // Added error state

    // --- Define Backend URL ---
    // Use environment variable if available, otherwise default
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

    // --- Fetch Subscription Data ---
    const fetchSubscriptionData = async (customerId: string) => {
        setError(null); // Clear previous errors
        try {
            console.log(`Fetching subscription for customer: ${customerId}`);
            const response = await fetch(`${API_BASE_URL}/api/subscription/${customerId}`);
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
                throw new Error(`Failed to fetch subscription: ${errorData.detail || response.statusText}`);
            }
            const data = await response.json();
            console.log("Subscription data received:", data);

            if (data.subscription) {
                const sub = data.subscription;
                setSubscription({
                    id: sub.id,
                    status: sub.status,
                    // Attempt to get plan name from nickname, product name, or default
                    plan: sub.items?.data[0]?.price?.nickname || sub.items?.data[0]?.price?.product?.name || 'Unknown Plan',
                    currentPeriodEnd: sub.current_period_end, // Keep as timestamp for potential future logic
                    cancel_at_period_end: sub.cancel_at_period_end,
                });
            } else {
                console.log("No active subscription found for customer.");
                setSubscription(null);
            }
        } catch (err: any) {
            console.error("Error fetching subscription:", err);
            setError(err.message || 'Could not fetch subscription details.');
            setSubscription(null); // Clear subscription on error
        }
    };

    // --- Fetch Payment History ---
    const fetchPaymentHistory = async (customerId: string) => {
        setError(null);
        try {
            console.log(`Fetching payment history for customer: ${customerId}`);
            const response = await fetch(`${API_BASE_URL}/api/payment-history/${customerId}`);
            if (!response.ok) {
                 const errorData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
                throw new Error(`Failed to fetch payment history: ${errorData.detail || response.statusText}`);
            }
            const data = await response.json();
            console.log("Payment history data received:", data);

            // Map the backend response to the PaymentHistoryItem interface
            const formattedPayments: PaymentHistoryItem[] = data.payments.map((p: any) => ({
                id: p.id,
                date: p.date, // Keep timestamp from backend
                amount: p.amount, // Amount is already correct from backend
                currency: p.currency,
                status: p.status,
                description: p.description || `Payment ${p.id.substring(0, 8)}...`,
                receiptUrl: p.receipt_url,
                pdfUrl: p.pdf_url,
            }));
            setPayments(formattedPayments);
        } catch (err: any) {
            console.error("Error fetching payment history:", err);
            setError(err.message || 'Could not fetch payment history.');
            setPayments([]); // Clear payments on error
        } finally {
             setLoading(false); // Stop loading indicator here, after both fetches attempt
        }
    };

    // --- Handle Cancel Subscription ---
    const handleCancelSubscription = async () => {
        if (!subscription || !subscription.id) {
            alert('No active subscription found to cancel.');
            return;
        }

        if (!window.confirm('Are you sure you want to cancel your subscription? It will remain active until the end of the current billing period.')) {
            return;
        }
        setError(null);
        setLoading(true); // Indicate activity

        try {
            console.log(`Requesting cancellation for subscription: ${subscription.id}`);
            const response = await fetch(`${API_BASE_URL}/api/cancel-subscription`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ subscription_id: subscription.id }) // Match backend Pydantic model
            });

            if (!response.ok) {
                 const errorData = await response.json().catch(() => ({ detail: 'Unknown cancellation error' }));
                 throw new Error(`Failed to cancel subscription: ${errorData.detail || response.statusText}`);
            }

            const result = await response.json();
            console.log("Cancellation response:", result);
            alert('Subscription cancellation requested. It will be cancelled at the end of the current billing period.');

            // Re-fetch subscription data to show updated status
            const customerId = localStorage.getItem('stripeCustomerId');
            if (customerId) {
                await fetchSubscriptionData(customerId); // Wait for refetch
            }
        } catch (err: any) {
            console.error("Error cancelling subscription:", err);
            setError(err.message || 'Failed to cancel subscription.');
            alert(`Error: ${err.message || 'Failed to cancel subscription.'}`); // Show error to user
        } finally {
            setLoading(false); // Stop loading indicator
        }
    };

    // --- useEffect Hook ---
    useEffect(() => {
        // --- Get customerId from localStorage ---
        const customerId = localStorage.getItem('stripeCustomerId');
        console.log(`Retrieved customerId from localStorage: ${customerId}`);

        if (!customerId) {
            setError("Customer ID not found in local storage. Please complete a purchase first.");
            setLoading(false);
            return; // Stop if no customer ID
        }

        setLoading(true);
        // Fetch data using the customerId - run fetches sequentially or in parallel
        const fetchData = async () => {
            await fetchSubscriptionData(customerId);
            await fetchPaymentHistory(customerId); // fetchPaymentHistory now sets loading to false
        };
        fetchData();

    }, []); // Empty dependency array means this runs once on mount

    // --- Render Logic ---
    if (loading) {
        return <div className="container">Loading customer data...</div>;
    }

    // Display error message if any occurred during loading
    if (error && !subscription && payments.length === 0) { // Show critical error if nothing loaded
        return <div className="container error-message">Error: {error} <Link to="/" className="button">Go back</Link></div>;
    }

    return (
        <div className="container">
            <h1>User Cabinet</h1>
            {/* Display non-critical errors */}
            {error && <div className="error-message">Notice: {error}</div>}

            {/* Subscription Section */}
            <section className="subscription-section">
                <h2>Current Subscription</h2>
                {subscription ? (
                    <div className="subscription-details">
                        <p><strong>Plan:</strong> {subscription.plan}</p>
                        <p><strong>Status:</strong> <span className={`status-${subscription.status}`}>{subscription.status}</span></p>
                        <p><strong>{subscription.cancel_at_period_end ? 'Expires on:' : 'Renews on:'}</strong> {formatDate(subscription.currentPeriodEnd)}</p>

                        {/* Show cancel button only for active, non-scheduled-for-cancellation subscriptions */}
                        {subscription.status === 'active' && !subscription.cancel_at_period_end && (
                            <button
                                onClick={handleCancelSubscription}
                                className="button button-danger"
                                disabled={loading} // Disable button while loading
                            >
                                {loading ? 'Processing...' : 'Cancel Subscription'}
                            </button>
                        )}
                         {/* Indicate if cancellation is pending */}
                         {subscription.cancel_at_period_end && (
                            <p className="warning-text">Cancellation scheduled for {formatDate(subscription.currentPeriodEnd)}</p>
                         )}
                    </div>
                ) : (
                    <p>No active subscription found.</p>
                )}
            </section>

            {/* Payment History Section */}
            <section className="payment-history">
                <h2>Payment History</h2>
                {payments.length > 0 ? (
                    <table>
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Description</th>
                                <th>Amount</th>
                                <th>Status</th>
                                <th>Receipt</th>
                            </tr>
                        </thead>
                        <tbody>
                            {payments.map(payment => (
                                <tr key={payment.id}>
                                    <td>{formatDate(payment.date)}</td>
                                    <td>{payment.description}</td>
                                    <td>{formatCurrency(payment.amount, payment.currency)}</td>
                                    <td><span className={`status-${payment.status}`}>{payment.status}</span></td>
                                    <td>
                                        {/* Provide links to receipt or PDF if available */}
                                        {payment.receiptUrl && <a href={payment.receiptUrl} target="_blank" rel="noopener noreferrer" className="link">View Receipt</a>}
                                        {payment.pdfUrl && <a href={payment.pdfUrl} target="_blank" rel="noopener noreferrer" className="link" style={{ marginLeft: payment.receiptUrl ? '5px' : '0' }}>(Invoice PDF)</a>}
                                        {!payment.receiptUrl && !payment.pdfUrl && '-'}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                ) : (
                     <p>No payment history found.</p>
                )}
            </section>

            <Link to="/" className="button">Go back to Start</Link>
        </div>
    );
};

export default CabinetPlaceholder;
