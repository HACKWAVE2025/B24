import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Users, TrendingUp, Shield, MessageSquare } from 'lucide-react';
import { getGlobalAnalytics } from '../services/analytics';

const GlobalStats = ({ darkMode }) => {
    const [analytics, setAnalytics] = useState({
        total_transactions: 0,
        total_users: 0,
        scams_detected: 0,
        feedback_count: 0
    });

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchAnalytics = async () => {
            try {
                setLoading(true);
                const data = await getGlobalAnalytics();
                setAnalytics(data);
                setError(null);
            } catch (err) {
                setError('Failed to load global analytics data');
                console.error('Global analytics error:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchAnalytics();

        // Refresh analytics every 5 minutes (300 seconds)
        const interval = setInterval(fetchAnalytics, 300000);

        return () => clearInterval(interval);
    }, []);

    if (loading) {
        return (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                {[...Array(4)].map((_, index) => (
                    <div key={index} className={`rounded-xl p-6 ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
                        <div className="animate-pulse">
                            <div className="h-6 bg-gray-300 dark:bg-gray-600 rounded w-1/3 mb-4"></div>
                            <div className="h-8 bg-gray-300 dark:bg-gray-600 rounded w-1/2"></div>
                        </div>
                    </div>
                ))}
            </div>
        );
    }

    if (error) {
        return (
            <div className={`rounded-xl p-6 mb-8 ${darkMode ? 'bg-red-900/30 border border-red-800' : 'bg-red-50 border border-red-200'}`}>
                <p className={darkMode ? "text-red-200" : "text-red-700"}>{error}</p>
            </div>
        );
    }

    const statCards = [
        {
            title: "Total Transactions",
            value: analytics.total_transactions.toLocaleString(),
            icon: <TrendingUp className="w-6 h-6" />,
            color: "text-blue-500",
            bg: darkMode ? "bg-blue-900/30" : "bg-blue-50",
            border: darkMode ? "border-blue-800" : "border-blue-200"
        },
        {
            title: "Total Users",
            value: analytics.total_users.toLocaleString(),
            icon: <Users className="w-6 h-6" />,
            color: "text-purple-500",
            bg: darkMode ? "bg-purple-900/30" : "bg-purple-50",
            border: darkMode ? "border-purple-800" : "border-purple-200"
        },
        {
            title: "Scams Detected",
            value: analytics.scams_detected.toLocaleString(),
            icon: <Shield className="w-6 h-6" />,
            color: "text-red-500",
            bg: darkMode ? "bg-red-900/30" : "bg-red-50",
            border: darkMode ? "border-red-800" : "border-red-200"
        },
        {
            title: "Feedback Received",
            value: analytics.feedback_count.toLocaleString(),
            icon: <MessageSquare className="w-6 h-6" />,
            color: "text-green-500",
            bg: darkMode ? "bg-green-900/30" : "bg-green-50",
            border: darkMode ? "border-green-800" : "border-green-200"
        }
    ];

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {statCards.map((card, index) => (
                <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1, duration: 0.4 }}
                    className={`rounded-xl p-6 shadow-lg border ${card.bg} ${card.border}`}
                >
                    <div className="flex items-center justify-between">
                        <div>
                            <p className={`text-sm font-medium ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                                {card.title}
                            </p>
                            <p className={`text-2xl font-bold mt-1 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                                {card.value}
                            </p>
                        </div>
                        <div className={`p-3 rounded-lg ${card.bg.replace('30', '20')}`}>
                            {card.icon}
                        </div>
                    </div>
                </motion.div>
            ))}
        </div>
    );
};

export default GlobalStats;