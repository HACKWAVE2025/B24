import { useState } from 'react';
import { motion } from 'framer-motion';
import { Shield, Mail, Lock, Eye, EyeOff, ArrowLeft, Moon, Sun } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';

const AuthPage = ({ onLogin, darkMode, toggleDarkMode }) => {
  const navigate = useNavigate();
  const [isSignUp, setIsSignUp] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: ''
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (isSignUp) {
      toast.success('Account created successfully!');
    } else {
      toast.success('Logged in successfully!');
    }
    onLogin();
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
              className="w-full bg-gradient-to-r from-indigo-600 via-blue-600 to-cyan-600 hover:from-indigo-700 hover:via-blue-700 hover:to-cyan-700 text-white font-semibold h-12 text-lg rounded-xl shadow-lg shadow-indigo-500/40"
            >
              {isSignUp ? 'Create Account' : 'Sign In'}
            </Button>
          </form>

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
