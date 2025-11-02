import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import Sidebar from '../components/Sidebar';
import TopNav from '../components/TopNav';
import DashboardCard from '../components/DashboardCard';
import TransactionHistory from '../components/TransactionHistory';
import { Shield, AlertTriangle, Users, TrendingUp } from 'lucide-react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { getUserAnalytics, getGlobalAnalytics } from '../services/analytics';
import { Progress } from '../components/ui/progress';

const DashboardPage = ({ onLogout, darkMode, toggleDarkMode }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [analytics, setAnalytics] = useState({
    total_transactions: 0,
    scams_prevented: 0,
    feedback_count: 0,
    accuracy: 94 // This would need to be calculated from real data
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setLoading(true);
        // Get user-specific analytics
        const userAnalytics = await getUserAnalytics();
        // Get global analytics for additional data
        const globalAnalytics = await getGlobalAnalytics();
        
        setAnalytics({
          total_transactions: userAnalytics.total_transactions,
          scams_prevented: userAnalytics.scams_prevented,
          feedback_count: userAnalytics.feedback_count,
          accuracy: 94 // This would need to be calculated from real data
        });
        setError(null);
      } catch (err) {
        setError('Failed to load analytics data');
        console.error('Analytics error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
    
    // Refresh analytics every 5 minutes (300 seconds)
    const interval = setInterval(fetchAnalytics, 300000);
    
    return () => clearInterval(interval);
  }, []);

  const stats = [
    {
      icon: <Shield className="w-6 h-6" />,
      label: "Total Analyzed",
      value: analytics.total_transactions.toLocaleString(),
      color: "#00C896",
      trend: "+12%"
    },
    {
      icon: <AlertTriangle className="w-6 h-6" />,
      label: "Scams Prevented",
      value: analytics.scams_prevented.toLocaleString(),
      color: "#FF6B6B",
      trend: "+8%"
    },
    {
      icon: <Users className="w-6 h-6" />,
      label: "User Reports",
      value: analytics.feedback_count.toLocaleString(),
      color: "#0091FF",
      trend: "+15%"
    },
    {
      icon: <TrendingUp className="w-6 h-6" />,
      label: "Accuracy",
      value: `${analytics.accuracy}%`,
      color: "#A78BFA",
      trend: "+2%"
    }
  ];

  const agentPerformance = [
    { name: 'Pattern Agent', accuracy: 96, predictions: 1245, color: '#00C896' },
    { name: 'Network Agent', accuracy: 94, predictions: 1189, color: '#0091FF' },
    { name: 'Behavior Agent', accuracy: 89, predictions: 1056, color: '#A78BFA' },
    { name: 'Biometric Agent', accuracy: 92, predictions: 1134, color: '#F472B6' }
  ];

  const riskDistribution = [
    { name: 'High Risk', value: 342, color: '#FF6B6B' },
    { name: 'Medium Risk', value: 567, color: '#FFB946' },
    { name: 'Low Risk', value: 891, color: '#00C896' }
  ];

  // Cumulative risk score for current transaction
  const currentTransactionRisk = 72;

  if (loading) {
    return (
      <div className={darkMode ? "min-h-screen bg-gray-900" : "min-h-screen bg-[#F8FAFB]"}>
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} onLogout={onLogout} />
        <TopNav onMenuClick={() => setSidebarOpen(true)} darkMode={darkMode} onDarkModeToggle={toggleDarkMode} />

        <section className="pt-24 pb-20 px-6">
          <div className="max-w-7xl mx-auto">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
              {[...Array(4)].map((_, index) => (
                <div key={index} className={`rounded-xl p-6 ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
                  <div className="animate-pulse">
                    <div className="h-6 bg-gray-300 dark:bg-gray-600 rounded w-1/3 mb-4"></div>
                    <div className="h-8 bg-gray-300 dark:bg-gray-600 rounded w-1/2"></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>
    );
  }

  if (error) {
    return (
      <div className={darkMode ? "min-h-screen bg-gray-900" : "min-h-screen bg-[#F8FAFB]"}>
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} onLogout={onLogout} />
        <TopNav onMenuClick={() => setSidebarOpen(true)} darkMode={darkMode} onDarkModeToggle={toggleDarkMode} />

        <section className="pt-24 pb-20 px-6">
          <div className="max-w-7xl mx-auto">
            <div className={`rounded-xl p-6 mb-8 ${darkMode ? 'bg-red-900/30 border border-red-800' : 'bg-red-50 border border-red-200'}`}>
              <p className={darkMode ? "text-red-200" : "text-red-700"}>{error}</p>
            </div>
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className={darkMode ? "min-h-screen bg-gray-900" : "min-h-screen bg-[#F8FAFB]"}>
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} onLogout={onLogout} />
      <TopNav onMenuClick={() => setSidebarOpen(true)} darkMode={darkMode} onDarkModeToggle={toggleDarkMode} />

      <section className="pt-24 pb-20 px-6" data-testid="dashboard-section">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="mb-12"
          >
            <h1 className={darkMode ? "text-4xl sm:text-5xl font-bold mb-4 text-white" : "text-4xl sm:text-5xl font-bold mb-4 text-gray-900"}>Analytics Dashboard</h1>
            <p className={darkMode ? "text-gray-300 text-lg" : "text-gray-600 text-lg"}>Real-time insights from FIGMENT's collective intelligence</p>
          </motion.div>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
            {stats.map((stat, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1, duration: 0.5 }}
              >
                <DashboardCard {...stat} darkMode={darkMode} />
              </motion.div>
            ))}
          </div>

          {/* Current Transaction Risk Score */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="glass p-8 rounded-2xl mb-12"
            data-testid="current-risk-section"
          >
            <h3 className={darkMode ? "text-2xl font-bold mb-6 text-white" : "text-2xl font-bold mb-6 text-gray-900"}>Cumulative Risk Score - Current Transaction</h3>
            <div className="grid md:grid-cols-2 gap-8 items-center">
              <div>
                <div className="relative w-64 h-64 mx-auto">
                  <svg className="w-full h-full -rotate-90">
                    <circle cx="128" cy="128" r="120" fill="none" stroke="#E2E8F0" strokeWidth="16" />
                    <circle
                      cx="128"
                      cy="128"
                      r="120"
                      fill="none"
                      stroke={currentTransactionRisk >= 70 ? '#FF6B6B' : currentTransactionRisk >= 40 ? '#FFB946' : '#00C896'}
                      strokeWidth="16"
                      strokeLinecap="round"
                      strokeDasharray={2 * Math.PI * 120}
                      strokeDashoffset={2 * Math.PI * 120 * (1 - currentTransactionRisk / 100)}
                      style={{ filter: `drop-shadow(0 0 12px ${currentTransactionRisk >= 70 ? '#FF6B6B' : currentTransactionRisk >= 40 ? '#FFB946' : '#00C896'})` }}
                    />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-6xl font-bold" style={{ color: currentTransactionRisk >= 70 ? '#FF6B6B' : currentTransactionRisk >= 40 ? '#FFB946' : '#00C896' }}>
                      {currentTransactionRisk}%
                    </span>
                    <span className="text-sm text-gray-600 mt-2">Risk Level</span>
                  </div>
                </div>
              </div>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between mb-2">
                    <span className={darkMode ? "text-sm font-medium text-gray-300" : "text-sm font-medium text-gray-700"}>Overall Assessment</span>
                    <span className="text-sm font-bold" style={{ color: currentTransactionRisk >= 70 ? '#FF6B6B' : currentTransactionRisk >= 40 ? '#FFB946' : '#00C896' }}>
                      {currentTransactionRisk >= 70 ? 'HIGH RISK' : currentTransactionRisk >= 40 ? 'MEDIUM RISK' : 'LOW RISK'}
                    </span>
                  </div>
                  <Progress value={currentTransactionRisk} className="h-3" />
                </div>
                <div className={darkMode ? "bg-gray-800 p-4 rounded-lg" : "bg-gray-50 p-4 rounded-lg"}>
                  <p className={darkMode ? "text-sm text-gray-300 leading-relaxed" : "text-sm text-gray-700 leading-relaxed"}>
                    Based on analysis from 4 AI agents, this transaction shows {currentTransactionRisk >= 70 ? 'strong indicators of potential fraud' : currentTransactionRisk >= 40 ? 'moderate risk factors' : 'minimal risk factors'}.
                    {currentTransactionRisk >= 70 && ' We strongly recommend canceling this transaction.'}
                  </p>
                </div>
              </div>
            </div>
          </motion.div>

          {/* AI Agents Analytics */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="glass p-8 rounded-2xl mb-12"
            data-testid="ai-agents-section"
          >
            <h3 className={darkMode ? "text-2xl font-bold mb-6 text-white" : "text-2xl font-bold mb-6 text-gray-900"}>AI Agents Performance Analytics</h3>
            <div className="grid lg:grid-cols-2 gap-8">
              {/* Bar Chart */}
              <div>
                <h4 className={darkMode ? "text-lg font-semibold mb-4 text-gray-200" : "text-lg font-semibold mb-4 text-gray-800"}>Prediction Accuracy by Agent</h4>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={agentPerformance}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                    <XAxis dataKey="name" angle={-15} textAnchor="end" height={80} tick={{ fill: '#64748B', fontSize: 12 }} />
                    <YAxis tick={{ fill: '#64748B' }} />
                    <Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #E2E8F0', borderRadius: '8px' }} />
                    <Bar dataKey="accuracy" radius={[8, 8, 0, 0]}>
                      {agentPerformance.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Agent Cards */}
              <div className="space-y-3">
                <h4 className={darkMode ? "text-lg font-semibold mb-4 text-gray-200" : "text-lg font-semibold mb-4 text-gray-800"}>Total Predictions</h4>
                {agentPerformance.map((agent, index) => (
                  <div key={index} className={darkMode ? "flex items-center justify-between p-4 bg-gray-800 rounded-lg hover:shadow-md transition-shadow" : "flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:shadow-md transition-shadow"}>
                    <div className="flex items-center gap-3">
                      <div className="w-3 h-3 rounded-full" style={{ backgroundColor: agent.color }}></div>
                      <span className={darkMode ? "font-medium text-gray-200" : "font-medium text-gray-800"}>{agent.name}</span>
                    </div>
                    <div className="text-right">
                      <div className={darkMode ? "text-lg font-bold text-white" : "text-lg font-bold text-gray-900"}>{agent.predictions.toLocaleString()}</div>
                      <div className={darkMode ? "text-xs text-gray-400" : "text-xs text-gray-600"}>{agent.accuracy}% accurate</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>

          {/* Risk Distribution */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="glass p-8 rounded-2xl mb-12"
            data-testid="risk-distribution-section"
          >
            <h3 className={darkMode ? "text-2xl font-bold mb-6 text-white" : "text-2xl font-bold mb-6 text-gray-900"}>Risk Level Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={riskDistribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={120}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {riskDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #E2E8F0', borderRadius: '8px' }} />
              </PieChart>
            </ResponsiveContainer>
          </motion.div>

          {/* User Activity */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="glass p-6 rounded-2xl"
            data-testid="user-activity"
          >
            <TransactionHistory userId={localStorage.getItem('figment_user_id')} darkMode={darkMode} />
          </motion.div>
        </div>
      </section>
    </div>
  );
};

export default DashboardPage;