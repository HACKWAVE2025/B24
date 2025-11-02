import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Brain, AlertTriangle, CheckCircle, Clock } from 'lucide-react';

const RealTimeAnalysis = ({ analysisResults, darkMode }) => {
    if (!analysisResults || analysisResults.length === 0) {
        return null;
    }

    const getRiskLevel = (riskScore) => {
        if (riskScore >= 70) return 'high';
        if (riskScore >= 40) return 'medium';
        return 'low';
    };

    const getRiskColor = (riskLevel) => {
        switch (riskLevel) {
            case 'high': return 'text-red-500';
            case 'medium': return 'text-orange-500';
            case 'low': return 'text-green-500';
            default: return 'text-gray-500';
        }
    };

    const getRiskIcon = (riskLevel) => {
        switch (riskLevel) {
            case 'high': return <AlertTriangle className="w-5 h-5 text-red-500" />;
            case 'medium': return <AlertTriangle className="w-5 h-5 text-orange-500" />;
            case 'low': return <CheckCircle className="w-5 h-5 text-green-500" />;
            default: return <Clock className="w-5 h-5 text-gray-500" />;
        }
    };

    return (
        <div className="mt-6">
            <h3 className={darkMode ? "text-xl font-semibold mb-4 text-white" : "text-xl font-semibold mb-4 text-gray-900"}>
                Real-Time Analysis Results
            </h3>

            <div className="space-y-4">
                {analysisResults.map((result, index) => {
                    const riskLevel = getRiskLevel(result.overallRisk);
                    const transaction = result.transaction || {};

                    return (
                        <motion.div
                            key={index}
                            initial={{ opacity: 0, x: 30 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: index * 0.1, duration: 0.4 }}
                            className={darkMode ? "glass border border-gray-700 rounded-xl p-4" : "glass border border-gray-200 rounded-xl p-4"}
                        >
                            <div className="flex items-start justify-between mb-3">
                                <div className="flex items-center gap-2">
                                    {getRiskIcon(riskLevel)}
                                    <span className={`font-semibold ${getRiskColor(riskLevel)}`}>
                                        {riskLevel.charAt(0).toUpperCase() + riskLevel.slice(1)} Risk
                                    </span>
                                </div>
                                <span className={darkMode ? "text-sm text-gray-400" : "text-sm text-gray-500"}>
                                    {transaction.time || 'Just now'}
                                </span>
                            </div>

                            <div className="mb-3">
                                <p className={darkMode ? "text-gray-300 font-mono text-sm" : "text-gray-700 font-mono text-sm"}>
                                    {transaction.receiver || 'Unknown recipient'}
                                </p>
                                <p className={darkMode ? "text-gray-400 text-sm" : "text-gray-600 text-sm"}>
                                    ₹{transaction.amount?.toLocaleString() || '0'} • {transaction.reason || 'No message'}
                                </p>
                            </div>

                            {result.aiExplanation && result.aiExplanation.length > 0 && result.aiExplanation !== "Sorry, unable to generate explanation at this time." && (
                                <div className={darkMode ? "bg-gray-700/50 border border-gray-600 rounded-lg p-3 mt-2" : "bg-blue-50 border border-blue-200 rounded-lg p-3 mt-2"}>
                                    <div className="flex items-center gap-2 mb-1">
                                        <Brain className={`w-4 h-4 ${darkMode ? 'text-blue-400' : 'text-blue-600'}`} />
                                        <span className={darkMode ? "text-xs font-semibold text-blue-400" : "text-xs font-semibold text-blue-600"}>
                                            AI Insight
                                        </span>
                                    </div>
                                    <p className={darkMode ? "text-gray-300 text-xs" : "text-gray-700 text-xs"}>
                                        {result.aiExplanation}
                                    </p>
                                </div>
                            )}

                            <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                                <span className={darkMode ? "text-sm text-gray-400" : "text-sm text-gray-500"}>
                                    Overall Risk: {result.overallRisk}%
                                </span>
                                <div className="w-24 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                    <div
                                        className={`h-full ${riskLevel === 'high' ? 'bg-red-500' :
                                                riskLevel === 'medium' ? 'bg-orange-500' : 'bg-green-500'
                                            }`}
                                        style={{ width: `${Math.min(result.overallRisk, 100)}%` }}
                                    />
                                </div>
                            </div>
                        </motion.div>
                    );
                })}
            </div>
        </div>
    );
};

export default RealTimeAnalysis;