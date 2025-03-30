import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom'; // Import useSearchParams
import { initiateCheckout, BACKEND_URL } from '../utils/checkout'; // Import BACKEND_URL

const SubscriptionPage: React.FC = () => {
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);
    const [searchParams] = useSearchParams(); // Hook to read URL params

    // --- Effect to handle session ID and save customer ID ---
    useEffect(() => {
        const sessionId = searchParams.get('session_id');
        const product = searchParams.get('product'); // Get product type if needed

        // Only run if session_id is present (meaning we came from a successful checkout)
        if (sessionId) {
            console.log(`Detected session_id: ${sessionId} for product: ${product}`);
            // Check if customerId is already saved for this session to avoid redundant calls
            const savedCustomerId = localStorage.getItem('stripeCustomerId');
            const processedSessionId = localStorage.getItem('processedSessionId');

            if (savedCustomerId && processedSessionId === sessionId) {
                 console.log(`Customer ID ${savedCustomerId} already saved for session ${sessionId}.`);
                 return; // Already processed this session
            }

            const fetchCustomerId = async () => {
                setLoading(true); // Indicate loading while fetching customer ID
                setError(null);
                try {
                    console.log(`Fetching customer ID for session: ${sessionId}`);
                    const response = await fetch(`${BACKEND_URL}/api/checkout-session/${sessionId}`);
                    if (!response.ok) {
                        const errorData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
                        throw new Error(`Failed to fetch session details: ${errorData.detail || response.statusText}`);
                    }
                    const data = await response.json();
                    if (data.customer_id) {
                        console.log(`Saving customer ID: ${data.customer_id} to localStorage.`);
                        localStorage.setItem('stripeCustomerId', data.customer_id);
                        localStorage.setItem('processedSessionId', sessionId); // Mark session as processed
                        // Optionally: Display a success message or trigger other actions
                    } else {
                        throw new Error("Customer ID not found in session response.");
                    }
                } catch (err: any) {
                    console.error("Error fetching/saving customer ID:", err);
                    setError(err.message || 'Could not retrieve customer details from session.');
                    // Clear potentially outdated info if fetch fails
                    localStorage.removeItem('stripeCustomerId');
                    localStorage.removeItem('processedSessionId');
                } finally {
                    setLoading(false); // Stop loading indicator
                }
            };

            fetchCustomerId();
        }
    }, [searchParams]); // Re-run if searchParams change

    return (
        <div className="container">
            <h1>Choose Your Subscription</h1>
            <p>Select a plan to get full access.</p>
            <div className="button-group">
                <button
                    onClick={() => initiateCheckout('monthly', setLoading, setError)}
                    disabled={loading}
                    className="button"
                >
                    {loading ? 'Processing...' : 'Subscribe Monthly ($10)'}
                </button>
                <button
                    onClick={() => initiateCheckout('yearly', setLoading, setError)}
                    disabled={loading}
                    className="button"
                >
                    {loading ? 'Processing...' : 'Subscribe Yearly ($100)'}
                </button>
                 {/* Optionally add a skip button if logic allows */}
                 {/* <button onClick={() => navigate('/upsell/coach')} disabled={loading} className="button button-secondary">Skip</button> */}
            </div>
            {error && <p className="error-message">Error: {error}</p>}
        </div>
    );
};

export default SubscriptionPage;
