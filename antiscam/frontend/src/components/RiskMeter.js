import { motion } from 'framer-motion';
import { Progress } from './ui/progress';

const RiskMeter = ({ score, darkMode }) => {
  const getColor = (score) => {
    if (score >= 70) return '#FF6B6B';
    if (score >= 40) return '#FFB946';
    return '#00C896';
  };

  const getRiskLevel = (score) => {
    if (score >= 70) return 'HIGH RISK';
    if (score >= 40) return 'MEDIUM RISK';
    return 'LOW RISK';
  };

  const color = getColor(score);
  const riskLevel = getRiskLevel(score);

  return (
    <div className="glass p-6 rounded-xl" data-testid="risk-meter">
      <div className="flex items-center justify-between mb-4">
        <h3 className={darkMode ? "text-lg font-semibold text-white" : "text-lg font-semibold text-gray-900"}>Overall Risk Score</h3>
        <span
          className="px-4 py-2 rounded-full font-bold text-sm"
          style={{ backgroundColor: `${color}20`, color: color }}
          data-testid="risk-level-badge"
        >
          {riskLevel}
        </span>
      </div>

      <div className="flex items-center justify-center py-8">
        <div className="relative w-48 h-48">
          <svg className="w-full h-full -rotate-90">
            <circle cx="96" cy="96" r="88" fill="none" stroke={darkMode ? "#374151" : "#E2E8F0"} strokeWidth="12" />
            <motion.circle
              cx="96"
              cy="96"
              r="88"
              fill="none"
              stroke={color}
              strokeWidth="12"
              strokeLinecap="round"
              strokeDasharray={2 * Math.PI * 88}
              initial={{ strokeDashoffset: 2 * Math.PI * 88 }}
              animate={{ strokeDashoffset: 2 * Math.PI * 88 * (1 - score / 100) }}
              transition={{ duration: 1, ease: 'easeOut' }}
              style={{ filter: `drop-shadow(0 0 8px ${color})` }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <motion.span
              initial={{ opacity: 0, scale: 0.5 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="text-5xl font-bold"
              style={{ color: color }}
              data-testid="risk-score-value"
            >
              {score}%
            </motion.span>
            <span className={darkMode ? "text-sm text-gray-400 mt-1" : "text-sm text-gray-600 mt-1"}>Risk Level</span>
          </div>
        </div>
      </div>

      <div className="mt-4">
        <div className={darkMode ? "flex justify-between text-xs text-gray-400 mb-2" : "flex justify-between text-xs text-gray-600 mb-2"}>
          <span>Safe</span>
          <span>Risky</span>
        </div>
        <Progress value={score} className="h-3" style={{ '--progress-color': color }} />
      </div>
    </div>
  );
};

export default RiskMeter;
