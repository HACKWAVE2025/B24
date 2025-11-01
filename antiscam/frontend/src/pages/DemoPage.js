import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSearchParams } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import TopNav from '../components/TopNav';
import TransactionForm from '../components/TransactionForm';
import ResultsModal from '../components/ResultsModal';
import PINEntry from '../components/PINEntry';
import FeedbackModal from '../components/FeedbackModal';
import { analyzeTransaction as analyzeTransactionAPI, completeTransaction, submitFeedback } from '../services/api';
import { toast } from 'sonner';

const DemoPage = ({ onLogout }) => {
  const [searchParams] = useSearchParams();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [results, setResults] = useState(null);
  const [showResults, setShowResults] = useState(false);
  const [showProceedWarning, setShowProceedWarning] = useState(false);
  const [showPINEntry, setShowPINEntry] = useState(false);
  const [showFeedback, setShowFeedback] = useState(false);
  const [currentTransaction, setCurrentTransaction] = useState(null);
  const [completedTxId, setCompletedTxId] = useState(null);
  const [userId] = useState(() => {
    // Generate persistent user ID
    let uid = localStorage.getItem('figment_user_id');
    if (!uid) {
      uid = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem('figment_user_id', uid);
    }
    return uid;
  });

  const handleAnalyze = async (formData) => {
    setIsAnalyzing(true);
    setShowResults(false);
    
    // Add user_id to transaction data
    const transactionData = {
      ...formData,
      user_id: userId
    };
    setCurrentTransaction(transactionData);
    
    try {
      // Call backend API
      const analysisResults = await analyzeTransactionAPI(transactionData);
      setResults(analysisResults);
      setShowResults(true);
    } catch (error) {
      toast.error('Failed to analyze transaction. Please try again.');
      console.error('Analysis error:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleCancel = () => {
    toast.success('Transaction cancelled successfully!');
    setShowResults(false);
    setResults(null);
    setCurrentTransaction(null);
  };

  const handleProceed = () => {
    // Close results modal first, then show warning
    setShowResults(false);
    // Small delay to allow modal close animation
    setTimeout(() => {
      setShowProceedWarning(true);
    }, 100);
  };

  const handleProceedConfirm = () => {
    // User confirmed - show PIN entry
    setShowProceedWarning(false);
    // Small delay to allow warning close animation
    setTimeout(() => {
      setShowPINEntry(true);
    }, 100);
  };

  const handlePINComplete = async (pin) => {
    // PIN entered - complete transaction
    setShowPINEntry(false);
    
    try {
      const now = new Date();
      const timeStr = now.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true 
      });

      const txData = {
        receiver: currentTransaction.upiId,
        amount: parseFloat(currentTransaction.amount),
        reason: currentTransaction.message || '',
        user_id: userId,
        time: timeStr,
        risk_score: results?.overallRisk || 0
      };

      const result = await completeTransaction(txData);
      setCompletedTxId(result.transaction_id);
      
      toast.success('Transaction completed successfully!');
      
      // Show feedback if risk was detected
      if (results?.overallRisk >= 40) {
        setTimeout(() => {
          setShowFeedback(true);
        }, 1000);
      } else {
        // Reset everything after safe transaction
        setTimeout(() => {
          setResults(null);
          setCurrentTransaction(null);
          setCompletedTxId(null);
        }, 2000);
      }
    } catch (error) {
      toast.error('Failed to complete transaction. Please try again.');
      console.error('Transaction completion error:', error);
    }
  };

  const handleFeedbackSubmit = async (feedbackData) => {
    try {
      await submitFeedback({
        transaction_id: completedTxId,
        receiver: currentTransaction.upiId,
        user_id: userId,
        was_scam: feedbackData.was_scam,
        comment: feedbackData.comment
      });

      if (feedbackData.was_scam) {
        toast.success('Thank you for reporting! This helps protect others.');
      } else {
        toast.success('Thank you for your feedback!');
      }

      setShowFeedback(false);
      
      // Reset everything
      setTimeout(() => {
        setResults(null);
        setCurrentTransaction(null);
        setCompletedTxId(null);
      }, 1000);
    } catch (error) {
      toast.error('Failed to submit feedback. Please try again.');
      console.error('Feedback error:', error);
    }
  };

  const handleReport = async () => {
    if (!currentTransaction) return;
    
    try {
      // Call backend API to report scam
      const { reportScam } = await import('../services/api');
      await reportScam({
        receiver: currentTransaction.upiId,
        reason: `High risk scam detected (Risk: ${results?.overallRisk || 'N/A'}%)`
      });
      
      toast.success('Scam reported! Thank you for helping protect the community.');
    } catch (error) {
      toast.error('Failed to report scam. Please try again.');
      console.error('Report error:', error);
    }
  };

  return (
    <div className="min-h-screen bg-[#F8FAFB]">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} onLogout={onLogout} />
      <TopNav onMenuClick={() => setSidebarOpen(true)} />
      
      <section className="pt-32 pb-20 px-6" data-testid="demo-section">
        <div className="max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center mb-12"
          >
            <h1 className="text-4xl sm:text-5xl font-bold mb-4 text-gray-900">Try FIGMENT Live Demo</h1>
            <p className="text-gray-600 text-lg">Enter transaction details to see AI analysis in action</p>
          </motion.div>

          <TransactionForm 
            onAnalyze={handleAnalyze} 
            isAnalyzing={isAnalyzing}
            initialData={{
              upi_id: searchParams.get('upi_id') || '',
              amount: searchParams.get('amount') || '',
              message: searchParams.get('message') || ''
            }}
          />

          {/* Analyzing Animation */}
          <AnimatePresence>
            {isAnalyzing && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="mt-8 glass p-8 rounded-2xl text-center"
                data-testid="analyzing-indicator"
              >
                <div className="flex flex-col items-center gap-4">
                  <div className="w-16 h-16 border-4 border-[#E0F7F4] border-t-[#00C896] rounded-full animate-spin"></div>
                  <div>
                    <p className="text-xl font-semibold text-[#00C896] mb-2">Analyzing Transaction...</p>
                    <p className="text-sm text-gray-600">AI agents are scanning for risks</p>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <ResultsModal
            isOpen={showResults}
            results={results}
            onCancel={handleCancel}
            onProceed={handleProceed}
            onReport={handleReport}
            onClose={() => setShowResults(false)}
          />

          {/* Proceed Warning Dialog */}
          <AnimatePresence mode="wait">
            {showProceedWarning && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 backdrop-blur-sm"
                onClick={() => setShowProceedWarning(false)}
              >
                <motion.div
                  initial={{ scale: 0.9, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0.9, opacity: 0 }}
                  onClick={(e) => e.stopPropagation()}
                  className="glass p-6 rounded-2xl max-w-md w-full mx-4 border-2 border-orange-500/30"
                >
                  <h3 className="text-xl font-bold mb-2 text-gray-900">⚠️ Scam Detected</h3>
                  <p className="text-gray-600 mb-4">
                    Our AI detected a potential scam with {results?.overallRisk || 'high'}% risk. 
                    Are you sure you want to proceed?
                  </p>
                  <div className="flex gap-3">
                    <button
                      onClick={() => setShowProceedWarning(false)}
                      className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                    >
                      Go Back
                    </button>
                    <button
                      onClick={handleProceedConfirm}
                      className="flex-1 px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600"
                    >
                      Proceed Anyway
                    </button>
                  </div>
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* PIN Entry */}
          <AnimatePresence mode="wait">
            {showPINEntry && (
              <PINEntry
                isOpen={showPINEntry}
                onComplete={handlePINComplete}
                onCancel={() => {
                  setShowPINEntry(false);
                  // Return to results modal
                  setTimeout(() => {
                    setShowResults(true);
                  }, 100);
                }}
                receiver={currentTransaction?.upiId}
                amount={currentTransaction?.amount}
              />
            )}
          </AnimatePresence>

          {/* Feedback Modal */}
          <FeedbackModal
            isOpen={showFeedback}
            onClose={() => {
              setShowFeedback(false);
              setResults(null);
              setCurrentTransaction(null);
              setCompletedTxId(null);
            }}
            onSubmit={handleFeedbackSubmit}
            receiver={currentTransaction?.upiId}
            riskScore={results?.overallRisk}
          />

          {/* Demo Tips */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3, duration: 0.6 }}
            className="mt-12 glass p-6 rounded-2xl"
          >
            <h3 className="text-lg font-semibold text-blue-600 mb-3">💡 Try These Examples</h3>
            <div className="grid md:grid-cols-2 gap-4 text-sm">
              <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                <p className="text-gray-700 font-semibold mb-2">High Risk Example:</p>
                <p className="text-gray-600 font-mono text-xs">UPI: kycupdate@okaxis</p>
                <p className="text-gray-600 font-mono text-xs">Message: "KYC verification fee"</p>
              </div>
              <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                <p className="text-gray-700 font-semibold mb-2">Safe Transaction:</p>
                <p className="text-gray-600 font-mono text-xs">UPI: friend@paytm</p>
                <p className="text-gray-600 font-mono text-xs">Message: "Lunch split"</p>
              </div>
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  );
};

export default DemoPage;
