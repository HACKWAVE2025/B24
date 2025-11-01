import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Shield, Eye, Network, User, ArrowRight, Zap, Brain, Lock, TrendingUp, BarChart3, Activity, Sparkles, Star, Moon, Sun } from 'lucide-react';
import { Button } from '../components/ui/button';

const LandingPage = ({ darkMode, toggleDarkMode }) => {
  const navigate = useNavigate();

  const features = [
    {
      icon: <Brain className="w-6 h-6" />,
      title: "AI-Powered Detection",
      description: "4 specialized AI agents work together to analyze every transaction in real-time",
      gradient: "from-indigo-500 to-blue-500"
    },
    {
      icon: <Zap className="w-6 h-6" />,
      title: "Instant Analysis",
      description: "Get risk assessment in seconds before completing any UPI transaction",
      gradient: "from-blue-500 to-cyan-500"
    },
    {
      icon: <Lock className="w-6 h-6" />,
      title: "Preventive Security",
      description: "Stop scams before they happen, not after you've lost money",
      gradient: "from-cyan-500 to-sky-500"
    },
    {
      icon: <BarChart3 className="w-6 h-6" />,
      title: "Smart Analytics",
      description: "Track trends and patterns to stay ahead of emerging scam techniques",
      gradient: "from-sky-500 to-indigo-500"
    }
  ];

  const agents = [
    { icon: <Eye className="w-8 h-8" />, name: "Pattern Agent", desc: "Detects scam patterns", color: "#4F46E5", bgGradient: "from-indigo-500/20 to-indigo-600/10" },
    { icon: <Network className="w-8 h-8" />, name: "Network Agent", desc: "Analyzes reputation", color: "#3B82F6", bgGradient: "from-blue-500/20 to-blue-600/10" },
    { icon: <User className="w-8 h-8" />, name: "Behavior Agent", desc: "Learns your patterns", color: "#06B6D4", bgGradient: "from-cyan-500/20 to-cyan-600/10" },
    { icon: <Shield className="w-8 h-8" />, name: "Biometric Agent", desc: "Detects pressure tactics", color: "#0EA5E9", bgGradient: "from-sky-500/20 to-sky-600/10" }
  ];

  const stats = [
    { value: "1,800+", label: "Transactions Analyzed", icon: <Activity className="w-5 h-5" /> },
    { value: "342", label: "Scams Prevented", icon: <Shield className="w-5 h-5" /> },
    { value: "94%", label: "Accuracy Rate", icon: <Star className="w-5 h-5" /> },
    { value: "567", label: "Community Reports", icon: <TrendingUp className="w-5 h-5" /> }
  ];

  return (
    <div className={darkMode ? "min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 pattern-dots" : "min-h-screen bg-gradient-to-br from-[#EEF2FF] via-[#F5F8FF] to-[#E0F2FE] pattern-dots"}>
      {/* Navbar */}
      <nav className="fixed top-0 left-0 right-0 z-50 glass-dark border-b border-indigo-200/50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 bg-gradient-to-br from-indigo-600 to-blue-500 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-500/30">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <span className="text-2xl font-bold text-indigo-600 dark:text-white">FIGMENT</span>
          </div>
          <div className="flex items-center gap-4">
            <Button
              onClick={toggleDarkMode}
              variant="ghost"
              className="text-gray-700 hover:text-indigo-600 hover:bg-indigo-50"
              data-testid="dark-mode-toggle"
            >
              {darkMode ? <Sun className="w-5 h-5 text-yellow-400" /> : <Moon className="w-5 h-5" />}
            </Button>
            <Button
              onClick={() => navigate('/auth')}
              variant="ghost"
              className="text-gray-700 hover:text-indigo-600 hover:bg-indigo-50"
              data-testid="login-btn"
            >
              Login
            </Button>
            <Button
              onClick={() => navigate('/auth')}
              className="bg-gradient-to-r from-indigo-600 via-blue-600 to-cyan-600 hover:from-indigo-700 hover:via-blue-700 hover:to-cyan-700 text-white font-semibold px-6 rounded-full shadow-lg shadow-indigo-500/40 hover:shadow-xl hover:shadow-indigo-500/50"
              data-testid="signup-btn"
            >
              Sign Up Free
            </Button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6 relative overflow-hidden">
        {/* Animated background elements */}
        <div className="absolute top-20 -left-32 w-[500px] h-[500px] bg-gradient-to-br from-indigo-400/30 via-blue-400/20 to-transparent rounded-full blur-3xl animate-float"></div>
        <div className="absolute top-40 -right-32 w-[600px] h-[600px] bg-gradient-to-bl from-blue-400/25 via-cyan-400/20 to-transparent rounded-full blur-3xl" style={{ animation: 'float 10s ease-in-out infinite 2s' }}></div>
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[400px] h-[400px] bg-gradient-to-t from-indigo-300/20 to-transparent rounded-full blur-3xl" style={{ animation: 'float 12s ease-in-out infinite 4s' }}></div>

        <div className="max-w-6xl mx-auto relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-center"
          >
            <motion.div
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              transition={{ duration: 0.5 }}
              className="inline-block mb-6"
            >
              <div className="flex items-center gap-2 px-5 py-2 glass rounded-full border border-indigo-300/50 shadow-lg shadow-indigo-500/20">
                <Sparkles className="w-4 h-4 text-indigo-600" />
                <span className="text-sm font-semibold bg-gradient-to-r from-indigo-600 to-blue-600 bg-clip-text text-transparent">AI-Powered UPI Protection</span>
              </div>
            </motion.div>

            <h1 className={darkMode ? "text-5xl sm:text-6xl lg:text-7xl font-bold mb-6 leading-tight text-white" : "text-5xl sm:text-6xl lg:text-7xl font-bold mb-6 leading-tight text-gray-900"} data-testid="hero-title">
              Stop UPI Scams
              <br />
              <span className="text-indigo-600 animate-gradient">Before They Happen</span>
            </h1>

            <p className={darkMode ? "text-xl text-gray-300 mb-10 max-w-3xl mx-auto leading-relaxed" : "text-xl text-gray-600 mb-10 max-w-3xl mx-auto leading-relaxed"}>
              FIGMENT uses 4 specialized AI agents to analyze every transaction in real-time.
              Get instant risk assessment and protect your money with explainable AI.
            </p>

            <div className="flex gap-4 justify-center flex-wrap">
              <Button
                onClick={() => navigate('/auth')}
                className="bg-gradient-to-r from-indigo-600 via-blue-600 to-cyan-600 hover:from-indigo-700 hover:via-blue-700 hover:to-cyan-700 text-white font-bold px-12 py-7 text-lg rounded-full shadow-2xl shadow-indigo-500/50 hover:shadow-indigo-600/60 animate-pulse-glow"
                data-testid="get-started-btn"
              >
                Get Started Free
                <ArrowRight className="ml-2 w-5 h-5" />
              </Button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-20 max-w-5xl mx-auto">
              {stats.map((stat, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5 + index * 0.1, duration: 0.5 }}
                  className="glass p-6 rounded-2xl hover-lift card-shine border border-indigo-200/50"
                >
                  <div className="flex items-center justify-center gap-2 mb-3">
                    <div className="text-indigo-600">{stat.icon}</div>
                  </div>
                  <div className="text-4xl font-bold  mb-2">{stat.value}</div>
                  <div className="text-sm text-gray-600 font-medium">{stat.label}</div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-6 relative">
        <div className="absolute inset-0 pattern-grid opacity-50"></div>
        <div className="max-w-6xl mx-auto relative z-10">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className={darkMode ? "text-4xl sm:text-5xl font-bold mb-4 text-white" : "text-4xl sm:text-5xl font-bold mb-4 text-gray-900"}>Why Choose FIGMENT?</h2>
            <p className={darkMode ? "text-gray-300 text-lg max-w-2xl mx-auto" : "text-gray-600 text-lg max-w-2xl mx-auto"}>Advanced AI technology to keep your transactions safe</p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1, duration: 0.5 }}
                whileHover={{ y: -12, scale: 1.02 }}
                className="glass p-6 rounded-2xl hover-lift card-shine border border-indigo-200/50 relative overflow-hidden group"
              >
                <div className={`absolute inset-0 bg-gradient-to-br ${feature.gradient} opacity-0 group-hover:opacity-5 transition-opacity`}></div>
                <div className={`w-14 h-14 bg-gradient-to-br ${feature.gradient} rounded-xl flex items-center justify-center mb-4 shadow-lg`}>
                  <div className="text-white">{feature.icon}</div>
                </div>
                <h3 className={darkMode ? "text-xl font-bold mb-2 text-white" : "text-xl font-bold mb-2 text-gray-900"}>{feature.title}</h3>
                <p className={darkMode ? "text-gray-300 text-sm leading-relaxed" : "text-gray-600 text-sm leading-relaxed"}>{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* AI Agents Section */}
      <section className={darkMode ? "py-20 px-6 bg-gradient-to-br from-gray-800/50 to-gray-900/50" : "py-20 px-6 bg-gradient-to-br from-white/50 to-indigo-50/50"}>
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className={darkMode ? "text-4xl sm:text-5xl font-bold mb-4 text-white" : "text-4xl sm:text-5xl font-bold mb-4 text-gray-900"}>Meet Our AI Agents</h2>
            <p className={darkMode ? "text-gray-300 text-lg" : "text-gray-600 text-lg"}>4 specialized agents working together to protect you</p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {agents.map((agent, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1, duration: 0.5 }}
                whileHover={{ scale: 1.05, rotate: 2 }}
                className="glass p-8 rounded-3xl text-center card-shine border-2 relative overflow-hidden group"
                style={{ borderColor: agent.color }}
              >
                <div className={`absolute inset-0 bg-gradient-to-br ${agent.bgGradient} opacity-0 group-hover:opacity-100 transition-opacity`}></div>
                <div className="relative z-10">
                  <div className="w-20 h-20 mx-auto rounded-2xl flex items-center justify-center mb-4 shadow-xl" style={{ background: `linear-gradient(135deg, ${agent.color} 0%, ${agent.color}dd 100%)` }}>
                    <div className="text-white">{agent.icon}</div>
                  </div>
                  <h3 className={darkMode ? "text-lg font-bold mb-2 text-white" : "text-lg font-bold mb-2 text-gray-900"}>{agent.name}</h3>
                  <p className={darkMode ? "text-sm text-gray-300" : "text-sm text-gray-600"}>{agent.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 px-6">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className={darkMode ? "text-4xl sm:text-5xl font-bold mb-4 text-white" : "text-4xl sm:text-5xl font-bold mb-4 text-gray-900"}>How It Works</h2>
            <p className={darkMode ? "text-gray-300 text-lg" : "text-gray-600 text-lg"}>Simple, fast, and secure</p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-12">
            {[
              { step: "1", title: "Enter Transaction", desc: "Input your UPI transaction details", gradient: "from-indigo-600 to-blue-600" },
              { step: "2", title: "AI Analysis", desc: "4 agents analyze risk in real-time", gradient: "from-blue-600 to-cyan-600" },
              { step: "3", title: "Make Decision", desc: "Get clear explanation and choose wisely", gradient: "from-cyan-600 to-sky-600" }
            ].map((item, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.2, duration: 0.5 }}
                className="text-center relative"
              >
                <div className={`w-24 h-24 mx-auto mb-6 bg-gradient-to-br ${item.gradient} rounded-3xl flex items-center justify-center text-white text-4xl font-bold shadow-2xl hover-lift`} style={{ boxShadow: '0 20px 40px rgba(79, 70, 229, 0.3)' }}>
                  {item.step}
                </div>
                <h3 className={darkMode ? "text-2xl font-bold mb-3 text-white" : "text-2xl font-bold mb-3 text-gray-900"}>{item.title}</h3>
                <p className={darkMode ? "text-gray-300 text-lg" : "text-gray-600 text-lg"}>{item.desc}</p>
                {index < 2 && (
                  <div className="hidden md:block absolute top-12 -right-6 text-indigo-300">
                    <ArrowRight className="w-8 h-8" />
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="glass p-12 rounded-3xl text-center relative overflow-hidden border-2 border-indigo-300/50"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/10 via-blue-500/10 to-cyan-500/10"></div>
            <div className="relative z-10">
              <h2 className={darkMode ? "text-4xl font-bold mb-4 text-white" : "text-4xl font-bold mb-4 text-gray-900"}>Ready to Protect Your Money?</h2>
              <p className={darkMode ? "text-xl text-gray-300 mb-8" : "text-xl text-gray-600 mb-8"}>Join thousands who trust FIGMENT for safe UPI transactions</p>
              <Button
                onClick={() => navigate('/auth')}
                className="bg-gradient-to-r from-indigo-600 via-blue-600 to-cyan-600 hover:from-indigo-700 hover:via-blue-700 hover:to-cyan-700 text-white font-bold px-12 py-7 text-lg rounded-full shadow-2xl shadow-indigo-500/50"
              >
                Start Free Now
                <ArrowRight className="ml-2 w-5 h-5" />
              </Button>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className={darkMode ? "border-t border-gray-700 bg-gray-900/50 backdrop-blur-sm py-12 px-6" : "border-t border-gray-200 bg-gray-50/50 backdrop-blur-sm py-12 px-6"}>
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-indigo-600 to-blue-500 rounded-lg flex items-center justify-center shadow-lg">
                <Shield className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold ">FIGMENT</span>
            </div>
            <p className={darkMode ? "text-sm text-gray-400" : "text-sm text-gray-600"}>© 2025 FIGMENT. Built with AI for safer digital payments.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
