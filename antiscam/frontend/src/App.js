import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import LandingPage from "./pages/LandingPage";
import AuthPage from "./pages/AuthPage";
import DashboardPage from "./pages/DashboardPage";
import DemoPage from "./pages/DemoPage";
import AIAnalysisPage from "./pages/AIAnalysisPage";
import ThreatIntelDashboard from "./pages/ThreatIntelDashboard";
import { Toaster } from "./components/ui/sonner";
import { getToken, verifyToken, removeToken, removeUser } from "./services/auth";
import AlertNotification from "./components/AlertNotification";
import { SocketProvider, useSocketContext } from "./context/SocketContext";
import APP_ROUTES from "./routes";

// Alert Manager Component - Must be inside Router
function AlertManager({ isAuthenticated }) {
  const socketContext = useSocketContext();
  if (!isAuthenticated || !socketContext) {
    return null;
  }

  const { alerts, dismissAlert } = socketContext;
  const navigate = useNavigate(); // Now we can safely use useNavigate here


  const handleProceed = (path) => {
    navigate(path);
  };

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-3 max-w-md w-full">
      {alerts.map((alert, index) => (
        <div
          key={alert.id}
          style={{ 
            transform: `translateY(${index * 20}px)`,
            zIndex: 50 - index
          }}
        >
          <AlertNotification
            alert={alert}
            onDismiss={() => dismissAlert(alert.id)}
            onProceed={handleProceed}
          />
        </div>
      ))}
    </div>
  );
}

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    // Check user preference for dark mode
    const savedDarkMode = localStorage.getItem('figment_dark_mode') === 'true';
    setDarkMode(savedDarkMode);

    // Apply dark mode class to document
    if (savedDarkMode) {
      document.documentElement.classList.add('dark');
    }
  }, []);

  useEffect(() => {
    const checkAuth = async () => {
      const token = getToken();
      if (token) {
        // Verify token with backend
        const isValid = await verifyToken();
        if (isValid) {
          setIsAuthenticated(true);
        } else {
          // Token is invalid or server is down, clear it
          removeToken();
          removeUser();
          setIsAuthenticated(false);
        }
      } else {
        // No token, ensure user is logged out
        setIsAuthenticated(false);
      }
      setIsChecking(false);
    };

    checkAuth();
  }, []);

  // Note: Authentication persists across page refreshes
  // Tokens are stored in localStorage and will remain until:
  // 1. User explicitly logs out
  // 2. Token expires (handled by backend)
  // 3. Token is invalid (handled by verifyToken check on mount)

  const handleLogin = () => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    removeToken();
    removeUser();
    setIsAuthenticated(false);
  };

  const toggleDarkMode = () => {
    const newDarkMode = !darkMode;
    setDarkMode(newDarkMode);
    localStorage.setItem('figment_dark_mode', newDarkMode.toString());

    if (newDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  // Show loading state while checking authentication
  if (isChecking) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="App">
      <SocketProvider isAuthenticated={isAuthenticated}>
        <BrowserRouter>
          {/* Alert Notification System - Must be inside Router for useNavigate to work */}
          <AlertManager isAuthenticated={isAuthenticated} />
          
          <Routes>
            {/* Public Landing Page */}
            <Route path={APP_ROUTES.root} element={
              isAuthenticated ? <Navigate to={APP_ROUTES.dashboard} /> : <LandingPage darkMode={darkMode} toggleDarkMode={toggleDarkMode} />
            } />

            {/* Auth Page */}
            <Route path={APP_ROUTES.auth} element={
              isAuthenticated ? <Navigate to={APP_ROUTES.dashboard} /> : <AuthPage onLogin={handleLogin} darkMode={darkMode} toggleDarkMode={toggleDarkMode} />
            } />

            {/* Protected Routes */}
            <Route path={APP_ROUTES.dashboard} element={
              isAuthenticated ? <DashboardPage onLogout={handleLogout} darkMode={darkMode} toggleDarkMode={toggleDarkMode} /> : <Navigate to={APP_ROUTES.auth} />
            } />
            <Route path={APP_ROUTES.threatIntel} element={
              isAuthenticated ? <ThreatIntelDashboard onLogout={handleLogout} darkMode={darkMode} toggleDarkMode={toggleDarkMode} /> : <Navigate to={APP_ROUTES.auth} />
            } />
            <Route path={APP_ROUTES.demo} element={
              isAuthenticated ? <DemoPage onLogout={handleLogout} darkMode={darkMode} toggleDarkMode={toggleDarkMode} /> : <Navigate to={APP_ROUTES.auth} />
            } />
            <Route path={APP_ROUTES.aiAnalysis} element={
              isAuthenticated ? <AIAnalysisPage onLogout={handleLogout} darkMode={darkMode} toggleDarkMode={toggleDarkMode} /> : <Navigate to={APP_ROUTES.auth} />
            } />
          </Routes>
        </BrowserRouter>
      </SocketProvider>
      
      <Toaster richColors />
    </div>
  );
}

export default App;