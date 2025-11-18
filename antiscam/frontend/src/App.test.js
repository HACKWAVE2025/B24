import { render, screen, waitFor } from '@testing-library/react';
import App from './App';

jest.mock('./pages/LandingPage', () => () => <div>Landing Page Content</div>);
jest.mock('./pages/AuthPage', () => () => <div>Auth Page</div>);
jest.mock('./pages/DashboardPage', () => () => <div>Dashboard Page</div>);
jest.mock('./pages/DemoPage', () => () => <div>Demo Page</div>);
jest.mock('./pages/AIAnalysisPage', () => () => <div>AI Analysis Page</div>);
jest.mock('./pages/ThreatIntelDashboard', () => () => <div>Threat Intel Dashboard</div>);
jest.mock('./components/AlertNotification', () => () => null);
jest.mock('./components/ui/sonner', () => ({
  Toaster: () => null,
}));

test('renders landing page when user is not authenticated', async () => {
  render(<App />);
  const landingContent = await waitFor(() => screen.getByText(/Landing Page Content/i));
  expect(landingContent).toBeInTheDocument();
});
