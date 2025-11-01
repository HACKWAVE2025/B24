import { useState } from 'react';
import { motion } from 'framer-motion';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Loader2 } from 'lucide-react';

const TransactionForm = ({ onAnalyze, isAnalyzing, darkMode }) => {
  const [formData, setFormData] = useState({
    upiId: '',
    amount: '',
    message: ''
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (formData.upiId && formData.amount) {
      onAnalyze(formData);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="glass p-8 rounded-2xl"
      data-testid="transaction-form"
    >
      <div className="mb-6">
        <h3 className={darkMode ? "text-2xl font-semibold mb-2 text-white" : "text-2xl font-semibold mb-2 text-gray-900"}>Enter Transaction Details</h3>
        <p className={darkMode ? "text-sm text-gray-400" : "text-sm text-gray-600"}>Fill in the details below to analyze the transaction</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className={darkMode ? "block text-sm font-medium mb-2 text-gray-300" : "block text-sm font-medium mb-2 text-gray-700"}>Receiver UPI ID *</label>
          <Input
            data-testid="upi-id-input"
            type="text"
            placeholder="example@okaxis"
            value={formData.upiId}
            onChange={(e) => setFormData({ ...formData, upiId: e.target.value })}
            className={darkMode ? "bg-gray-700 border-gray-600 text-white placeholder:text-gray-400" : "bg-white border-gray-300 text-gray-900 placeholder:text-gray-400"}
            required
            disabled={isAnalyzing}
          />
        </div>

        <div>
          <label className={darkMode ? "block text-sm font-medium mb-2 text-gray-300" : "block text-sm font-medium mb-2 text-gray-700"}>Amount (₹) *</label>
          <Input
            data-testid="amount-input"
            type="number"
            placeholder="1000"
            value={formData.amount}
            onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
            className={darkMode ? "bg-gray-700 border-gray-600 text-white placeholder:text-gray-400" : "bg-white border-gray-300 text-gray-900 placeholder:text-gray-400"}
            required
            disabled={isAnalyzing}
          />
        </div>

        <div>
          <label className={darkMode ? "block text-sm font-medium mb-2 text-gray-300" : "block text-sm font-medium mb-2 text-gray-700"}>Message / Note</label>
          <Textarea
            data-testid="message-input"
            placeholder="Enter transaction description..."
            value={formData.message}
            onChange={(e) => setFormData({ ...formData, message: e.target.value })}
            className={darkMode ? "bg-gray-700 border-gray-600 text-white placeholder:text-gray-400 min-h-[100px]" : "bg-white border-gray-300 text-gray-900 placeholder:text-gray-400 min-h-[100px]"}
            disabled={isAnalyzing}
          />
        </div>

        <Button
          data-testid="analyze-btn"
          type="submit"
          disabled={isAnalyzing || !formData.upiId || !formData.amount}
          className="w-full bg-gradient-to-r from-[#00C896] to-[#0091FF] hover:from-[#00A077] hover:to-[#0075CC] text-white font-semibold py-6 text-lg rounded-xl shadow-lg"
        >
          {isAnalyzing ? (
            <>
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Analyzing...
            </>
          ) : (
            'Analyze Transaction'
          )}
        </Button>
      </form>
    </motion.div>
  );
};

export default TransactionForm;
