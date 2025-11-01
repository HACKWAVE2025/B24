import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Lock, ArrowRight } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';

const PINEntry = ({ isOpen, onComplete, onCancel, receiver, amount, darkMode }) => {
  const [pin, setPin] = useState(['', '', '', '', '', '']);
  const inputRefs = useRef([]);

  useEffect(() => {
    if (isOpen && inputRefs.current[0]) {
      inputRefs.current[0].focus();
    }
  }, [isOpen]);

  const handleChange = (index, value) => {
    if (value.length > 1) return; // Only allow single digit

    const newPin = [...pin];
    newPin[index] = value.replace(/\D/g, ''); // Only numbers
    setPin(newPin);

    // Auto-focus next input
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !pin[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    const newPin = [...pin];
    for (let i = 0; i < 6; i++) {
      newPin[i] = pastedData[i] || '';
    }
    setPin(newPin);
    if (pastedData.length >= 6) {
      inputRefs.current[5]?.focus();
    } else if (pastedData.length > 0) {
      inputRefs.current[pastedData.length]?.focus();
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const pinString = pin.join('');
    if (pinString.length === 6) {
      // Demo PIN - any 6 digits work
      onComplete(pinString);
    }
  };

  if (!isOpen) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[70] flex items-center justify-center bg-black/50 backdrop-blur-sm"
      onClick={onCancel}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
        className={darkMode ? "glass p-8 rounded-2xl max-w-md w-full mx-4 border-2 border-[#00C896]/30 bg-gray-800" : "glass p-8 rounded-2xl max-w-md w-full mx-4 border-2 border-[#00C896]/30"}
        data-testid="pin-entry-modal"
      >
        <div className="text-center mb-6">
          <div className="w-16 h-16 bg-gradient-to-br from-[#00C896] to-[#0091FF] rounded-full flex items-center justify-center mx-auto mb-4">
            <Lock className="w-8 h-8 text-white" />
          </div>
          <h2 className={darkMode ? "text-2xl font-bold mb-2 text-white" : "text-2xl font-bold mb-2 text-gray-900"}>Enter PIN</h2>
          <p className={darkMode ? "text-sm text-gray-400" : "text-sm text-gray-600"}>
            Confirm transaction to {receiver || 'receiver'}
          </p>
          <p className={darkMode ? "text-lg font-semibold text-white mt-2" : "text-lg font-semibold text-gray-900 mt-2"}>
            ₹{amount || '0'}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="flex justify-center gap-2">
            {pin.map((digit, index) => (
              <Input
                key={index}
                ref={(el) => (inputRefs.current[index] = el)}
                type="text"
                inputMode="numeric"
                maxLength={1}
                value={digit}
                onChange={(e) => handleChange(index, e.target.value)}
                onKeyDown={(e) => handleKeyDown(index, e)}
                onPaste={handlePaste}
                className={darkMode ? "w-12 h-14 text-center text-2xl font-bold border-2 border-gray-600 focus:border-[#00C896] focus:ring-[#00C896] bg-gray-700 text-white" : "w-12 h-14 text-center text-2xl font-bold border-2 border-gray-300 focus:border-[#00C896] focus:ring-[#00C896]"}
                data-testid={`pin-input-${index}`}
              />
            ))}
          </div>

          <div className="flex gap-3">
            <Button
              type="button"
              variant="outline"
              onClick={onCancel}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={pin.join('').length !== 6}
              className="flex-1 bg-gradient-to-r from-[#00C896] to-[#0091FF] hover:from-[#00A077] hover:to-[#0075CC] text-white"
            >
              Confirm
              <ArrowRight className="ml-2 w-4 h-4" />
            </Button>
          </div>

          <p className={darkMode ? "text-xs text-center text-gray-400" : "text-xs text-center text-gray-500"}>
            Demo: Enter any 6-digit PIN
          </p>
        </form>
      </motion.div>
    </motion.div>
  );
};

export default PINEntry;

