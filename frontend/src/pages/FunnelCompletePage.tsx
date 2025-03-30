import React from 'react';
import { Link } from 'react-router-dom';
// import { useSearchParams } from 'react-router-dom'; // Keep if needed later

const FunnelCompletePage: React.FC = () => {
    // You could potentially check searchParams here for context about what was purchased
    // const [searchParams] = useSearchParams();
    // const lastProduct = searchParams.get('product');
    // const sessionId = searchParams.get('session_id');

    return (
        <div className="container">
            <h1>Setup Complete!</h1>
            <p>Thank you! You have completed the initial setup.</p>
            {/* In a real app, this would link to the actual user cabinet */}
            <Link to="/cabinet-placeholder" className="button">Go to My Cabinet</Link>
        </div>
    );
};

export default FunnelCompletePage;
