import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useState, useEffect } from "react";
import LandingPage from "./pages/LandingPage";
import AuthPage from "./pages/AuthPage";
import DashboardPage from "./pages/DashboardPage";
import DemoPage from "./pages/DemoPage";
import AIAnalysisPage from "./pages/AIAnalysisPage";
import { Toaster } from "./components/ui/sonner";
import { getToken, verifyToken, removeToken, removeUser } from "./services/auth";

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      const token = getToken();
      if (token) {
        // Verify token with backend
        const isValid = await verifyToken();
        if (isValid) {
          setIsAuthenticated(true);
        } else {
          // Token is invalid, clear it
          removeToken();
          removeUser();
        }
      }
      setIsChecking(false);
    };
    
    checkAuth();
  }, []);

  const handleLogin = () => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    removeToken();
    removeUser();
    setIsAuthenticated(false);
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
      <BrowserRouter>
        <Routes>
          {/* Public Landing Page */}
          <Route path="/" element={
            isAuthenticated ? <Navigate to="/dashboard" /> : <LandingPage />
          } />
          
          {/* Auth Page */}
          <Route path="/auth" element={
            isAuthenticated ? <Navigate to="/dashboard" /> : <AuthPage onLogin={handleLogin} />
          } />
          
          {/* Protected Routes */}
          <Route path="/dashboard" element={
            isAuthenticated ? <DashboardPage onLogout={handleLogout} /> : <Navigate to="/auth" />
          } />
          <Route path="/demo" element={
            isAuthenticated ? <DemoPage onLogout={handleLogout} /> : <Navigate to="/auth" />
          } />
          <Route path="/ai-analysis" element={
            isAuthenticated ? <AIAnalysisPage onLogout={handleLogout} /> : <Navigate to="/auth" />
          } />
        </Routes>
      </BrowserRouter>
      <Toaster richColors />
    </div>
  );
}

export default App;
