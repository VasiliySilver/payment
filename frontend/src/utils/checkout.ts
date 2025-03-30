import React from 'react';

// Define the base URL for the backend API
export const BACKEND_URL = 'http://localhost:8000';

// --- Helper Function for Checkout ---
export const initiateCheckout = async (
    productType: string,
    setLoading: React.Dispatch<React.SetStateAction<boolean>>,
    setError: React.Dispatch<React.SetStateAction<string | null>>
) => {
    setLoading(true);
    setError(null);
    try {
        const response = await fetch(`${BACKEND_URL}/create-checkout-session`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ product_type: productType }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }

        const session = await response.json();
        window.location.href = session.url; // Redirect to Stripe

    } catch (err: any) {
        console.error(`Checkout error for ${productType}:`, err);
        setError(err.message || 'Failed to initiate checkout. Please try again.');
        setLoading(false);
    }
    // No setLoading(false) on success due to redirect
};
