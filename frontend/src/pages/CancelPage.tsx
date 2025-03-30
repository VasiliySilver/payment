import React from 'react';
import { useSearchParams, Link } from 'react-router-dom';

const CancelPage: React.FC = () => {
    const [searchParams] = useSearchParams();
    const cancelledProduct = searchParams.get('product');

    return (
        <div className="container">
            <h1>Payment Cancelled</h1>
            <p>Your payment process was cancelled{cancelledProduct ? ` for the ${cancelledProduct} offer` : ''}. You have not been charged.</p>
            <Link to="/" className="button">Go back to Start</Link>
        </div>
    );
};

export default CancelPage;
