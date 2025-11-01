import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Shield, Mail, Lock, Eye, EyeOff, ArrowLeft, Moon, Sun ,Loader2 } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';
import { signup, login, getCurrentUser } from '../services/auth';

const AuthPage = ({ onLogin, darkMode, toggleDarkMode }) => {
  const navigate = useNavigate();
  const [isSignUp, setIsSignUp] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: ''
  });

  // Handle OAuth callback from backend
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    const success = urlParams.get('success');
    const error = urlParams.get('error');
    
    if (error) {
      toast.error(`Google authentication failed: ${error}`);
      // Clean URL
      window.history.replaceState({}, document.title, '/auth');
      return;
    }
    
    if (token && success === 'true') {
      // Store token and user info
      localStorage.setItem('figment_token', token);
      
      // Get user info from backend
      handleOAuthCallback(token);
    }
  }, []);

  const handleOAuthCallback = async (token) => {
    try {
      setIsLoading(true);
      
      // Get user info from backend
      const result = await getCurrentUser();
      
      if (result) {
        localStorage.setItem('figment_user', JSON.stringify(result));
        toast.success('Logged in successfully with Google!');
        onLogin();
        navigate('/dashboard');
      } else {
        toast.error('Failed to get user information');
      }
    } catch (error) {
      toast.error('Failed to complete Google authentication');
    } finally {
      setIsLoading(false);
      // Clean URL
      window.history.replaceState({}, document.title, '/auth');
    }
  };

  const handleGoogleSignIn = () => {
    // Redirect to backend OAuth endpoint
    const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
    window.location.href = `${API_BASE_URL}/api/auth/google/redirect`;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      if (isSignUp) {
        const result = await signup(formData.name, formData.email, formData.password);
        if (result.success) {
          toast.success('Account created successfully!');
          onLogin();
          navigate('/dashboard');
        }
      } else {
        const result = await login(formData.email, formData.password);
        if (result.success) {
          toast.success('Logged in successfully!');
          onLogin();
          navigate('/dashboard');
        }
      }
    } catch (error) {
      const errorMessage = error.error || error.message || (isSignUp ? 'Signup failed' : 'Login failed');
      toast.error(errorMessage);
      console.error('Auth error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={darkMode ? "min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 pattern-dots flex items-center justify-center px-6 py-12" : "min-h-screen bg-gradient-to-br from-[#EEF2FF] via-[#F5F8FF] to-[#E0F2FE] pattern-dots flex items-center justify-center px-6 py-12"}>
      {/* Animated background */}
      <div className="absolute top-20 left-10 w-80 h-80 bg-gradient-to-br from-indigo-400/20 to-blue-400/10 rounded-full blur-3xl animate-float"></div>
      <div className="absolute bottom-20 right-10 w-96 h-96 bg-gradient-to-bl from-blue-400/20 to-cyan-400/10 rounded-full blur-3xl" style={{ animation: 'float 8s ease-in-out infinite' }}></div>

      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="w-full max-w-md relative z-10"
      >
        {/* Back button */}
        <div className="flex justify-between mb-4">
          <Button
            onClick={() => navigate('/')}
            variant="ghost"
            className="text-gray-600 hover:text-indigo-600 hover:bg-indigo-50"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Home
          </Button>
          <Button
            onClick={toggleDarkMode}
            variant="ghost"
            className="text-gray-600 hover:text-indigo-600 hover:bg-indigo-50"
            data-testid="dark-mode-toggle"
          >
            {darkMode ? <Sun className="w-4 h-4 text-yellow-400" /> : <Moon className="w-4 h-4" />}
          </Button>
        </div>

        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center gap-2 mb-4">
            <div className="w-12 h-12 bg-gradient-to-br from-indigo-600 to-blue-500 rounded-xl flex items-center justify-center shadow-2xl shadow-indigo-500/40">
              <Shield className="w-7 h-7 text-white" />
            </div>
            <span className="text-3xl font-bold text-gray-900 dark:text-white">FIGMENT</span>
          </div>
          <p className={darkMode ? "text-gray-300" : "text-gray-600"}>AI co-pilot for safe UPI transactions</p>
        </div>

        {/* Auth Card */}
        <div className="glass p-8 rounded-3xl shadow-2xl border border-indigo-200/50" data-testid="auth-form">
          <div className="text-center mb-6">
            <h2 className={darkMode ? "text-2xl font-bold mb-2 text-white" : "text-2xl font-bold mb-2 text-gray-900"}>{isSignUp ? 'Create Account' : 'Welcome Back'}</h2>
            <p className={darkMode ? "text-sm text-gray-300" : "text-sm text-gray-600"}>
              {isSignUp ? 'Sign up to get started with FIGMENT' : 'Sign in to continue protecting your transactions'}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {isSignUp && (
              <div>
                <label className={darkMode ? "block text-sm font-medium mb-2 text-gray-300" : "block text-sm font-medium mb-2 text-gray-700"}>Full Name</label>
                <Input
                  data-testid="name-input"
                  type="text"
                  placeholder="John Doe"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="bg-white/90 border-indigo-200 text-gray-900 h-12 focus:border-indigo-500 focus:ring-indigo-500"
                  required
                />
              </div>
            )}

            <div>
              <label className={darkMode ? "block text-sm font-medium mb-2 text-gray-300" : "block text-sm font-medium mb-2 text-gray-700"}>Email Address</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <Input
                  data-testid="email-input"
                  type="email"
                  placeholder="you@example.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="pl-11 bg-white/90 border-indigo-200 text-gray-900 h-12 focus:border-indigo-500 focus:ring-indigo-500"
                  required
                />
              </div>
            </div>

            <div>
              <label className={darkMode ? "block text-sm font-medium mb-2 text-gray-300" : "block text-sm font-medium mb-2 text-gray-700"}>Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <Input
                  data-testid="password-input"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="pl-11 pr-11 bg-white/90 border-indigo-200 text-gray-900 h-12 focus:border-indigo-500 focus:ring-indigo-500"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <Button
              data-testid="submit-btn"
              type="submit"
              disabled={isLoading}
              className="w-full bg-gradient-to-r from-indigo-600 via-blue-600 to-cyan-600 hover:from-indigo-700 hover:via-blue-700 hover:to-cyan-700 text-white font-semibold h-12 text-lg rounded-xl shadow-lg shadow-indigo-500/40 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  {isSignUp ? 'Creating Account...' : 'Signing In...'}
                </>
              ) : (
                isSignUp ? 'Create Account' : 'Sign In'
              )}
            </Button>
          </form>

          {/* Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-gray-500">Or continue with</span>
            </div>
          </div>

          {/* Google Sign In Button */}
          <div className="mb-4">
            <Button
              type="button"
              onClick={handleGoogleSignIn}
              disabled={isLoading}
              className="w-full bg-white hover:bg-gray-50 text-gray-700 font-medium h-12 text-base rounded-xl border-2 border-gray-300 flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
              Continue with Google
            </Button>
          </div>

          <div className="mt-6 text-center">
            <p className={darkMode ? "text-sm text-gray-300" : "text-sm text-gray-600"}>
              {isSignUp ? 'Already have an account?' : "Don't have an account?"}
              <button
                onClick={() => setIsSignUp(!isSignUp)}
                className="ml-2 font-semibold text-indigo-600 hover:text-indigo-700"
                data-testid="toggle-auth-btn"
              >
                {isSignUp ? 'Sign In' : 'Sign Up'}
              </button>
            </p>
          </div>
        </div>

        <p className={darkMode ? "text-center text-xs text-gray-400 mt-6" : "text-center text-xs text-gray-500 mt-6"}>
          By continuing, you agree to FIGMENT's Terms of Service and Privacy Policy
        </p>
      </motion.div>
    </div>
  );
};

export default AuthPage;
