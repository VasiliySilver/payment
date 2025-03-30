import { Routes, Route } from 'react-router-dom';
import './App.css';
import TrialPage from './pages/TrialPage';
import SubscriptionPage from './pages/SubscriptionPage';
import UpsellCoachPage from './pages/UpsellCoachPage';
import UpsellAssistantPage from './pages/UpsellAssistantPage';
import FunnelCompletePage from './pages/FunnelCompletePage';
import CancelPage from './pages/CancelPage';
import CabinetPlaceholder from './pages/CabinetPlaceholder';

// --- Main App Component with Routing ---

function App() {
    return (
        <Routes>
            <Route path="/" element={<TrialPage />} />
            <Route path="/subscription" element={<SubscriptionPage />} />
            <Route path="/upsell/coach" element={<UpsellCoachPage />} />
            <Route path="/upsell/assistant" element={<UpsellAssistantPage />} />
            <Route path="/funnel/complete" element={<FunnelCompletePage />} />
            <Route path="/cancel" element={<CancelPage />} />
            <Route path="/cabinet-placeholder" element={<CabinetPlaceholder />} />
            {/* Redirect any unknown paths back to the start */}
            <Route path="*" element={<TrialPage />} />
        </Routes>
    );
}

export default App;
