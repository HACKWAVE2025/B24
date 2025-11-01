import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Shield, Eye, Network, User, ArrowRight } from 'lucide-react';
import { Button } from '../components/ui/button';

const HomePage = ({ onLogout }) => {
  const navigate = useNavigate();

  const agents = [
    {
      icon: <Eye className="w-8 h-8" />,
      name: "Pattern Agent",
      description: "Detects known scam patterns and suspicious keywords",
      color: "#00C896"
    },
    {
      icon: <Network className="w-8 h-8" />,
      name: "Network Agent",
      description: "Analyzes receiver reputation across transaction network",
      color: "#0091FF"
    },
    {
      icon: <User className="w-8 h-8" />,
      name: "Behavior Agent",
      description: "Learns your normal patterns to detect anomalies",
      color: "#A78BFA"
    },
    {
      icon: <Shield className="w-8 h-8" />,
      name: "Biometric Agent",
      description: "Detects rushed decisions and pressure tactics",
      color: "#F472B6"
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#E0F7F4] via-[#F8FAFB] to-[#E0EFFF]">
      <div className="max-w-6xl mx-auto px-6 py-20">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center"
        >
          <div className="flex items-center justify-center gap-2 mb-8">
            <div className="w-16 h-16 bg-gradient-to-br from-[#00C896] to-[#0091FF] rounded-xl flex items-center justify-center">
              <Shield className="w-10 h-10 text-white" />
            </div>
            <span className="text-4xl font-bold text-gray-900">FIGMENT</span>
          </div>

          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold mb-6 leading-tight text-gray-900">
            Prevent UPI Scams
            <br />
            <span className="text-[#00C896]">Before They Happen</span>
          </h1>

          <p className="text-lg sm:text-xl text-gray-600 mb-10 max-w-2xl mx-auto">
            FIGMENT is your AI co-pilot for safe, smarter financial decisions.
            Real-time scam detection with explainable AI.
          </p>

          <div className="flex gap-4 justify-center flex-wrap">
            <Button
              onClick={() => navigate('/demo')}
              className="bg-gradient-to-r from-[#00C896] to-[#0091FF] hover:from-[#00A077] hover:to-[#0075CC] text-white font-semibold px-8 py-6 text-lg rounded-full shadow-lg"
            >
              Try Live Demo
              <ArrowRight className="ml-2 w-5 h-5" />
            </Button>
            <Button
              onClick={() => navigate('/dashboard')}
              variant="outline"
              className="border-2 border-[#00C896] text-[#00C896] hover:bg-[#00C896]/10 px-8 py-6 text-lg rounded-full"
            >
              View Dashboard
            </Button>
          </div>
        </motion.div>

        {/* Agents */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mt-20">
          {agents.map((agent, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 + 0.5, duration: 0.5 }}
              whileHover={{ y: -10, scale: 1.02 }}
              className="glass p-6 rounded-2xl"
              style={{ borderTop: `3px solid ${agent.color}` }}
            >
              <div
                className="w-16 h-16 rounded-xl flex items-center justify-center mb-4"
                style={{ backgroundColor: `${agent.color}20`, color: agent.color }}
              >
                {agent.icon}
              </div>
              <h3 className="text-xl font-semibold mb-2" style={{ color: agent.color }}>
                {agent.name}
              </h3>
              <p className="text-gray-600 text-sm">{agent.description}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default HomePage;
