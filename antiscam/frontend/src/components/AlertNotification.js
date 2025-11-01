import { useState } from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle, X, ArrowRight } from 'lucide-react';
import { Button } from './ui/button';

const AlertNotification = ({ alert, onDismiss, onProceed }) => {
  const [isVisible, setIsVisible] = useState(true);

  const handleDismiss = () => {
    setIsVisible(false);
    setTimeout(() => {
      onDismiss();
    }, 300);
  };

  const handleProceed = () => {
    // Navigate to demo page with alert data
    const params = new URLSearchParams({
      upi_id: alert.upi_id,
      amount: alert.amount.toString(),
      message: alert.message || ''
    });
    handleDismiss();
    // Small delay to allow animation to complete
    setTimeout(() => {
      if (onProceed) {
        onProceed(`/demo?${params.toString()}`);
      } else {
        // Fallback to window.location if navigation function not provided
        window.location.href = `/demo?${params.toString()}`;
      }
    }, 100);
  };

  if (!isVisible) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: -50, x: 300 }}
      animate={{ opacity: 1, y: 0, x: 0 }}
      exit={{ opacity: 0, x: 300 }}
      className="max-w-md w-full"
    >
      <div className="glass border-2 border-orange-300 bg-gradient-to-r from-orange-50 to-red-50 p-4 rounded-xl shadow-2xl">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 mt-1">
            <AlertTriangle className="w-6 h-6 text-orange-600" />
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-bold text-gray-900">New Transaction Alert</h3>
              <button
                onClick={handleDismiss}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            
            <div className="space-y-1 text-xs text-gray-700 mb-3">
              <p className="font-semibold">UPI ID: <span className="font-mono text-gray-900">{alert.upi_id}</span></p>
              <p className="font-semibold">Amount: <span className="font-mono text-gray-900">₹{alert.amount.toLocaleString('en-IN')}</span></p>
              <p className="text-gray-600 line-clamp-2">{alert.message}</p>
            </div>
            
            <Button
              onClick={handleProceed}
              className="w-full bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white text-sm font-semibold py-2 rounded-lg flex items-center justify-center gap-2"
            >
              Proceed to Transaction
              <ArrowRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default AlertNotification;

