import { useState } from 'react';
import { motion } from 'framer-motion';
import Sidebar from '../components/Sidebar';
import TopNav from '../components/TopNav';
import { LineChart, Line, AreaChart, Area, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { TrendingUp, Activity, Brain, Shield } from 'lucide-react';

const AIAnalysisPage = ({ onLogout, darkMode, toggleDarkMode }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const trendData = [
    { month: 'Jan', scams: 45, detected: 43, accuracy: 95.5 },
    { month: 'Feb', scams: 52, detected: 49, accuracy: 94.2 },
    { month: 'Mar', scams: 48, detected: 46, accuracy: 95.8 },
    { month: 'Apr', scams: 61, detected: 58, accuracy: 95.1 },
    { month: 'May', scams: 55, detected: 52, accuracy: 94.5 },
    { month: 'Jun', scams: 67, detected: 64, accuracy: 95.5 },
  ];

  const agentRadarData = [
    { metric: 'Pattern Recognition', patternAgent: 96, networkAgent: 88, behaviorAgent: 85, biometricAgent: 90 },
    { metric: 'Speed', patternAgent: 92, networkAgent: 95, behaviorAgent: 78, biometricAgent: 88 },
    { metric: 'Reliability', patternAgent: 94, networkAgent: 96, behaviorAgent: 89, biometricAgent: 91 },
    { metric: 'Learning Rate', patternAgent: 88, networkAgent: 85, behaviorAgent: 95, biometricAgent: 82 },
    { metric: 'False Positives', patternAgent: 4, networkAgent: 6, behaviorAgent: 11, biometricAgent: 8 },
  ];

  const confidenceOverTime = [
    { week: 'Week 1', confidence: 78 },
    { week: 'Week 2', confidence: 82 },
    { week: 'Week 3', confidence: 85 },
    { week: 'Week 4', confidence: 88 },
    { week: 'Week 5', confidence: 91 },
    { week: 'Week 6', confidence: 94 },
  ];

  return (
    <div className={darkMode ? "min-h-screen bg-gray-900" : "min-h-screen bg-[#F8FAFB]"}>
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} onLogout={onLogout} />
      <TopNav onMenuClick={() => setSidebarOpen(true)} darkMode={darkMode} onDarkModeToggle={toggleDarkMode} />

      <section className="pt-24 pb-20 px-6" data-testid="ai-analysis-section">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="mb-12"
          >
            <h1 className={darkMode ? "text-4xl sm:text-5xl font-bold mb-4 text-white" : "text-4xl sm:text-5xl font-bold mb-4 text-gray-900"}>AI Analysis & Insights</h1>
            <p className={darkMode ? "text-gray-300 text-lg" : "text-gray-600 text-lg"}>Deep dive into AI performance metrics and learning patterns</p>
          </motion.div>

          {/* Key Metrics */}
          <div className="grid md:grid-cols-4 gap-6 mb-12">
            {[
              { icon: <Brain className="w-6 h-6" />, label: 'AI Models Active', value: '4', color: '#00C896' },
              { icon: <Activity className="w-6 h-6" />, label: 'Predictions/Day', value: '2.3K', color: '#0091FF' },
              { icon: <TrendingUp className="w-6 h-6" />, label: 'Learning Rate', value: '94.2%', color: '#A78BFA' },
              { icon: <Shield className="w-6 h-6" />, label: 'Confidence Score', value: '96%', color: '#F472B6' },
            ].map((metric, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1, duration: 0.5 }}
                className="glass p-6 rounded-xl"
              >
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-12 h-12 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${metric.color}20`, color: metric.color }}>
                    {metric.icon}
                  </div>
                </div>
                <div className="text-3xl font-bold mb-1" style={{ color: metric.color }}>{metric.value}</div>
                <div className={darkMode ? "text-sm text-gray-400" : "text-sm text-gray-600"}>{metric.label}</div>
              </motion.div>
            ))}
          </div>

          {/* Scam Detection Trend */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="glass p-8 rounded-2xl mb-12"
            data-testid="detection-trend-chart"
          >
            <h3 className={darkMode ? "text-2xl font-bold mb-6 text-white" : "text-2xl font-bold mb-6 text-gray-900"}>Scam Detection Trend & Accuracy</h3>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" stroke={darkMode ? "#374151" : "#E2E8F0"} />
                <XAxis dataKey="month" tick={{ fill: darkMode ? '#9CA3AF' : '#64748B' }} />
                <YAxis yAxisId="left" tick={{ fill: darkMode ? '#9CA3AF' : '#64748B' }} />
                <YAxis yAxisId="right" orientation="right" tick={{ fill: darkMode ? '#9CA3AF' : '#64748B' }} />
                <Tooltip contentStyle={{ backgroundColor: darkMode ? '#1F2937' : 'white', border: darkMode ? '1px solid #374151' : '1px solid #E2E8F0', borderRadius: '8px', color: darkMode ? 'white' : 'black' }} />
                <Legend />
                <Line yAxisId="left" type="monotone" dataKey="scams" stroke="#FF6B6B" strokeWidth={3} name="Total Scams" dot={{ fill: '#FF6B6B', r: 5 }} />
                <Line yAxisId="left" type="monotone" dataKey="detected" stroke="#00C896" strokeWidth={3} name="Detected" dot={{ fill: '#00C896', r: 5 }} />
                <Line yAxisId="right" type="monotone" dataKey="accuracy" stroke="#0091FF" strokeWidth={2} name="Accuracy %" dot={{ fill: '#0091FF', r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </motion.div>

          {/* Agent Performance Radar */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="glass p-8 rounded-2xl mb-12"
            data-testid="agent-radar-chart"
          >
            <h3 className={darkMode ? "text-2xl font-bold mb-6 text-white" : "text-2xl font-bold mb-6 text-gray-900"}>AI Agents Performance Comparison</h3>
            <ResponsiveContainer width="100%" height={500}>
              <RadarChart data={agentRadarData}>
                <PolarGrid stroke={darkMode ? "#374151" : "#E2E8F0"} />
                <PolarAngleAxis dataKey="metric" tick={{ fill: darkMode ? '#9CA3AF' : '#64748B', fontSize: 12 }} />
                <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: darkMode ? '#9CA3AF' : '#64748B' }} />
                <Radar name="Pattern Agent" dataKey="patternAgent" stroke="#00C896" fill="#00C896" fillOpacity={0.3} />
                <Radar name="Network Agent" dataKey="networkAgent" stroke="#0091FF" fill="#0091FF" fillOpacity={0.3} />
                <Radar name="Behavior Agent" dataKey="behaviorAgent" stroke="#A78BFA" fill="#A78BFA" fillOpacity={0.3} />
                <Radar name="Biometric Agent" dataKey="biometricAgent" stroke="#F472B6" fill="#F472B6" fillOpacity={0.3} />
                <Legend />
                <Tooltip contentStyle={{ backgroundColor: darkMode ? '#1F2937' : 'white', border: darkMode ? '1px solid #374151' : '1px solid #E2E8F0', borderRadius: '8px', color: darkMode ? 'white' : 'black' }} />
              </RadarChart>
            </ResponsiveContainer>
          </motion.div>

          {/* Confidence Growth */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="glass p-8 rounded-2xl"
            data-testid="confidence-chart"
          >
            <h3 className={darkMode ? "text-2xl font-bold mb-6 text-white" : "text-2xl font-bold mb-6 text-gray-900"}>AI Confidence Score Growth</h3>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={confidenceOverTime}>
                <defs>
                  <linearGradient id="colorConfidence" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00C896" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#00C896" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={darkMode ? "#374151" : "#E2E8F0"} />
                <XAxis dataKey="week" tick={{ fill: darkMode ? '#9CA3AF' : '#64748B' }} />
                <YAxis domain={[70, 100]} tick={{ fill: darkMode ? '#9CA3AF' : '#64748B' }} />
                <Tooltip contentStyle={{ backgroundColor: darkMode ? '#1F2937' : 'white', border: darkMode ? '1px solid #374151' : '1px solid #E2E8F0', borderRadius: '8px', color: darkMode ? 'white' : 'black' }} />
                <Area type="monotone" dataKey="confidence" stroke="#00C896" strokeWidth={3} fillOpacity={1} fill="url(#colorConfidence)" />
              </AreaChart>
            </ResponsiveContainer>
            <div className={darkMode ? "mt-6 bg-green-900/30 p-4 rounded-lg border border-green-800" : "mt-6 bg-green-50 p-4 rounded-lg border border-green-200"}>
              <p className={darkMode ? "text-sm text-gray-300" : "text-sm text-gray-700"}>
                <span className={darkMode ? "font-semibold text-green-400" : "font-semibold text-green-700"}>Insight:</span> The AI confidence score has improved by 20% over the past 6 weeks through continuous learning from user feedback and new scam pattern detection.
              </p>
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  );
};

export default AIAnalysisPage;
