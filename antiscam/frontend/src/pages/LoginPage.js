import { useState } from 'react';
import { motion } from 'framer-motion';
import { Shield, Mail, Lock, Eye, EyeOff } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { toast } from 'sonner';

const LoginPage = ({ onLogin }) => {
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
    <div className="min-h-screen bg-gradient-to-br from-[#E0F7F4] via-[#F8FAFB] to-[#E0EFFF] flex items-center justify-center px-6 py-12">
      {/* Animated background elements */}
      <div className="absolute top-20 left-10 w-64 h-64 bg-[#00C896] opacity-10 rounded-full blur-3xl animate-float"></div>
      <div className="absolute bottom-20 right-10 w-96 h-96 bg-[#0091FF] opacity-10 rounded-full blur-3xl" style={{ animation: 'float 8s ease-in-out infinite' }}></div>

      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="w-full max-w-md relative z-10"
      >
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center gap-2 mb-4">
            <div className="w-12 h-12 bg-gradient-to-br from-[#00C896] to-[#0091FF] rounded-xl flex items-center justify-center">
              <Shield className="w-7 h-7 text-white" />
            </div>
            <span className="text-3xl font-bold ">FIGMENT</span>
          </div>
          <p className="text-gray-600">AI co-pilot for safe UPI transactions</p>
        </div>

        {/* Login/Signup Card */}
        <div className="glass p-8 rounded-2xl" data-testid="auth-form">
          <div className="text-center mb-6">
            <h2 className="text-2xl font-bold mb-2">{isSignUp ? 'Create Account' : 'Welcome Back'}</h2>
            <p className="text-sm text-gray-600">
              {isSignUp ? 'Sign up to get started' : 'Sign in to continue to FIGMENT'}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {isSignUp && (
              <div>
                <label className="block text-sm font-medium mb-2 text-gray-700">Full Name</label>
                <Input
                  data-testid="name-input"
                  type="text"
                  placeholder="John Doe"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="bg-white border-gray-300 text-gray-900"
                  required
                />
              </div>
            )}

            <div>
              <label className="block text-sm font-medium mb-2 text-gray-700">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <Input
                  data-testid="email-input"
                  type="email"
                  placeholder="you@example.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="pl-11 bg-white border-gray-300 text-gray-900"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2 text-gray-700">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <Input
                  data-testid="password-input"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="pl-11 pr-11 bg-white border-gray-300 text-gray-900"
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
              className="w-full bg-gradient-to-r from-[#00C896] to-[#0091FF] hover:from-[#00A077] hover:to-[#0075CC] text-white font-semibold py-6 text-lg rounded-xl shadow-lg"
            >
              {isSignUp ? 'Create Account' : 'Sign In'}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              {isSignUp ? 'Already have an account?' : "Don't have an account?"}
              <button
                onClick={() => setIsSignUp(!isSignUp)}
                className="ml-2 font-semibold text-[#00C896] hover:text-[#00A077]"
                data-testid="toggle-auth-btn"
              >
                {isSignUp ? 'Sign In' : 'Sign Up'}
              </button>
            </p>
          </div>
        </div>

        <p className="text-center text-xs text-gray-500 mt-6">
          By continuing, you agree to FIGMENT's Terms of Service and Privacy Policy
        </p>
      </motion.div>
    </div>
  );
};

export default LoginPage;
