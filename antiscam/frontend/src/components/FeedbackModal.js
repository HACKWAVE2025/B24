import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
import { Button } from './ui/button';
import { Dialog, DialogContent, DialogTitle, DialogDescription } from './ui/dialog';

const FeedbackModal = ({ isOpen, onClose, onSubmit, receiver, riskScore, darkMode }) => {
  const [wasScam, setWasScam] = useState(null);
  const [comment, setComment] = useState('');

  const handleSubmit = () => {
    if (wasScam !== null) {
      onSubmit({
        was_scam: wasScam,
        comment: comment.trim() || undefined
      });
      // Reset form
      setWasScam(null);
      setComment('');
    }
  };

  const handleClose = () => {
    setWasScam(null);
    setComment('');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className={darkMode ? "max-w-md bg-gray-800" : "max-w-md"} data-testid="feedback-modal">
        {/* Hidden title for accessibility */}
        <DialogTitle className="sr-only">Scam Detection Feedback</DialogTitle>
        {/* Hidden description for accessibility */}
        <DialogDescription className="sr-only">
          Provide feedback on whether the detected scam was real or not.
        </DialogDescription>
        <div className="text-center mb-6">
          <div className="w-16 h-16 bg-gradient-to-br from-orange-400 to-red-500 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertTriangle className="w-8 h-8 text-white" />
          </div>
          <h2 className={darkMode ? "text-2xl font-bold mb-2 text-white" : "text-2xl font-bold mb-2 text-gray-900"}>
            Scam Detected - Was it Real?
          </h2>
          <p className={darkMode ? "text-sm text-gray-400 mb-1" : "text-sm text-gray-600 mb-1"}>
            We detected a potential scam for:
          </p>
          <p className={darkMode ? "text-sm font-semibold text-white" : "text-sm font-semibold text-gray-900"}>{receiver}</p>
          <p className={darkMode ? "text-xs text-gray-400 mt-2" : "text-xs text-gray-500 mt-2"}>
            Risk Score: {riskScore}%
          </p>
        </div>

        <div className="space-y-4 mb-6">
          <div>
            <p className={darkMode ? "text-sm font-medium mb-3 text-gray-300" : "text-sm font-medium mb-3 text-gray-700"}>
              Was this actually a scam?
            </p>
            <div className="flex gap-3">
              <Button
                type="button"
                onClick={() => setWasScam(true)}
                className={`flex-1 ${wasScam === true
                  ? 'bg-red-600 hover:bg-red-700 text-white'
                  : 'bg-red-50 hover:bg-red-100 text-red-600 border border-red-200'
                  }`}
                data-testid="feedback-yes"
              >
                <XCircle className="w-4 h-4 mr-2" />
                Yes, it was a scam
              </Button>
              <Button
                type="button"
                onClick={() => setWasScam(false)}
                className={`flex-1 ${wasScam === false
                  ? 'bg-green-600 hover:bg-green-700 text-white'
                  : 'bg-green-50 hover:bg-green-100 text-green-600 border border-green-200'
                  }`}
                data-testid="feedback-no"
              >
                <CheckCircle className="w-4 h-4 mr-2" />
                No, it was safe
              </Button>
            </div>
          </div>

          {wasScam !== null && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="overflow-hidden"
            >
              <label className={darkMode ? "block text-sm font-medium mb-2 text-gray-300" : "block text-sm font-medium mb-2 text-gray-700"}>
                Additional Comment (Optional)
              </label>
              <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Share any additional details..."
                className={darkMode ? "w-full p-3 border border-gray-600 rounded-lg focus:ring-2 focus:ring-[#00C896] focus:border-[#00C896] resize-none bg-gray-700 text-white" : "w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#00C896] focus:border-[#00C896] resize-none"}
                rows={3}
                data-testid="feedback-comment"
              />
            </motion.div>
          )}
        </div>

        <div className="flex gap-3">
          <Button
            type="button"
            variant="outline"
            onClick={handleClose}
            className="flex-1"
          >
            Skip
          </Button>
          <Button
            type="button"
            onClick={handleSubmit}
            disabled={wasScam === null}
            className="flex-1 bg-gradient-to-r from-[#00C896] to-[#0091FF] hover:from-[#00A077] hover:to-[#0075CC] text-white disabled:opacity-50"
          >
            Submit Feedback
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default FeedbackModal;