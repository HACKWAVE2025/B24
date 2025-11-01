import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown } from 'lucide-react';

const DashboardCard = ({ icon, label, value, color, trend, darkMode }) => {
  const isPositive = trend && trend.startsWith('+');

  return (
    <motion.div
      whileHover={{ y: -5, scale: 1.02 }}
      className="glass p-6 rounded-xl"
      data-testid={`dashboard-card-${label.toLowerCase().replace(/ /g, '-')}`}
    >
      <div className="flex items-start justify-between mb-4">
        <div
          className="w-12 h-12 rounded-lg flex items-center justify-center"
          style={{
            backgroundColor: darkMode ? `${color}30` : `${color}20`,
            color: color
          }}
        >
          {icon}
        </div>
        {trend && (
          <div className={`flex items-center gap-1 text-xs font-semibold ${isPositive ? 'text-green-600' : 'text-red-600'
            }`}>
            {isPositive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
            {trend}
          </div>
        )}
      </div>
      <div>
        <div className="text-3xl font-bold mb-1" style={{ color: color }}>
          {value}
        </div>
        <div className="text-sm text-gray-600">{label}</div>
      </div>
    </motion.div>
  );
};

export default DashboardCard;
