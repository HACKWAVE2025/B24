import { motion, AnimatePresence } from 'framer-motion';
import { Dialog, DialogContent, DialogTitle, DialogDescription } from './ui/dialog';
import { Button } from './ui/button';
import AgentCard from './AgentCard';
import RiskMeter from './RiskMeter';
import { AlertTriangle } from 'lucide-react';

const ResultsModal = ({ isOpen, results, onCancel, onProceed, onReport, onClose, darkMode }) => {
  if (!results) return null;

  const handleProceedClick = () => {
    onClose(); // Close dialog first
    setTimeout(() => {
      onProceed(); // Then trigger proceed
    }, 100);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className={darkMode ? "max-w-4xl max-h-[90vh] overflow-y-auto bg-gray-800 border-2 border-[#00C896]/30 p-0" : "max-w-4xl max-h-[90vh] overflow-y-auto bg-white border-2 border-[#00C896]/30 p-0"} data-testid="results-modal">
        {/* Hidden title for accessibility */}
        <DialogTitle className="sr-only">Transaction Risk Analysis Results</DialogTitle>
        {/* Hidden description for accessibility */}
        <DialogDescription className="sr-only">
          View the AI analysis results for your transaction risk assessment.
        </DialogDescription>
        <div className={darkMode ? "sticky top-0 bg-gray-800 z-10 border-b border-gray-700 p-6" : "sticky top-0 bg-white z-10 border-b border-gray-200 p-6"}>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <AlertTriangle className={`w-8 h-8 ${results.overallRisk >= 70 ? 'text-red-500' :
                  results.overallRisk >= 40 ? 'text-orange-500' : 'text-green-500'
                  }`} />
                <h2 className={darkMode ? "text-2xl sm:text-3xl font-bold text-white" : "text-2xl sm:text-3xl font-bold text-gray-900"} data-testid="risk-title">
                  {results.overallRisk >= 70 ? 'High Risk Transaction!' :
                    results.overallRisk >= 40 ? 'Medium Risk Transaction' : 'Low Risk Transaction'}
                </h2>
              </div>
              <p className={darkMode ? "text-sm text-gray-400" : "text-sm text-gray-600"}>AI analysis complete</p>
            </div>
          </div>
        </div>

        <div className="p-6 space-y-6">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5 }}
          >
            <RiskMeter score={results.overallRisk} darkMode={darkMode} />
          </motion.div>

          <div>
            <h3 className={darkMode ? "text-xl font-semibold mb-4 text-white" : "text-xl font-semibold mb-4 text-gray-900"}>AI Agents Analysis</h3>
            <div className="space-y-4">
              {results.agents.map((agent, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -30 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1, duration: 0.4 }}
                >
                  <AgentCard agent={agent} darkMode={darkMode} />
                </motion.div>
              ))}
            </div>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.4 }}
            className="flex flex-col sm:flex-row gap-4 pt-6"
          >
            <Button
              data-testid="cancel-transaction-btn"
              onClick={onCancel}
              className="flex-1 bg-gradient-to-r from-[#00C896] to-[#0091FF] hover:from-[#00A077] hover:to-[#0075CC] text-white font-semibold py-6 text-lg rounded-xl"
            >
              Cancel Transaction (Safe Choice)
            </Button>
            <Button
              data-testid="proceed-anyway-btn"
              onClick={handleProceedClick}
              variant="outline"
              className="flex-1 border-2 border-orange-500 text-orange-600 hover:bg-orange-50 py-6 text-lg rounded-xl"
            >
              Proceed Anyway
            </Button>
          </motion.div>

          {results.overallRisk >= 70 && (
            <Button
              data-testid="report-scam-btn"
              onClick={onReport}
              variant="outline"
              className="w-full border-2 border-red-500 text-red-600 hover:bg-red-50 py-4 rounded-xl"
            >
              Report as Scam
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ResultsModal;