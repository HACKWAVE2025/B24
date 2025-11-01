import { useEffect, useState } from 'react';
import { getTransactionHistory } from '../services/api';

const TransactionHistory = ({ userId, darkMode }) => {
    const [transactions, setTransactions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchHistory = async () => {
            if (!userId) return;

            try {
                setLoading(true);
                const response = await getTransactionHistory(userId);
                setTransactions(response.transactions || []);
                setError(null);
            } catch (err) {
                setError('Failed to load transaction history');
                console.error('Error fetching transaction history:', err);
                setTransactions([]);
            } finally {
                setLoading(false);
            }
        };

        fetchHistory();
    }, [userId]);

    if (loading) {
        return (
            <div className="p-6 text-center">
                <p className={darkMode ? "text-gray-400" : "text-gray-500"}>Loading transaction history...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-6 text-center">
                <p className="text-red-500">{error}</p>
            </div>
        );
    }

    if (transactions.length === 0) {
        return (
            <div className="p-6 text-center">
                <p className={darkMode ? "text-gray-400" : "text-gray-500"}>No transactions found</p>
            </div>
        );
    }

    return (
        <div className={darkMode ? "bg-gray-800 rounded-lg shadow-sm border border-gray-700" : "bg-white rounded-lg shadow-sm border"}>
            <div className={darkMode ? "px-6 py-4 border-b bg-gray-700" : "px-6 py-4 border-b bg-gray-50"}>
                <h3 className={darkMode ? "text-lg font-semibold text-gray-100" : "text-lg font-semibold text-gray-900"}>Transaction History</h3>
            </div>
            <div className="overflow-x-auto">
                <table className="w-full">
                    <thead className={darkMode ? "bg-gray-700" : "bg-gray-50"}>
                        <tr>
                            <th className={darkMode ? "px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider" : "px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"}>Date</th>
                            <th className={darkMode ? "px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider" : "px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"}>Receiver</th>
                            <th className={darkMode ? "px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider" : "px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"}>Amount</th>
                            <th className={darkMode ? "px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider" : "px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"}>Reason</th>
                            <th className={darkMode ? "px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider" : "px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"}>Risk Score</th>
                        </tr>
                    </thead>
                    <tbody className={darkMode ? "bg-gray-800 divide-y divide-gray-700" : "bg-white divide-y divide-gray-200"}>
                        {transactions.map((tx) => (
                            <tr key={tx.id} className={darkMode ? "hover:bg-gray-700" : "hover:bg-gray-50"}>
                                <td className={darkMode ? "px-6 py-4 whitespace-nowrap text-sm text-gray-100" : "px-6 py-4 whitespace-nowrap text-sm text-gray-900"}>
                                    {new Date(tx.created_at).toLocaleDateString()}
                                </td>
                                <td className={darkMode ? "px-6 py-4 whitespace-nowrap text-sm text-gray-100 font-mono" : "px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-mono"}>
                                    {tx.receiver}
                                </td>
                                <td className={darkMode ? "px-6 py-4 whitespace-nowrap text-sm text-gray-100" : "px-6 py-4 whitespace-nowrap text-sm text-gray-900"}>
                                    ₹{tx.amount.toLocaleString()}
                                </td>
                                <td className={darkMode ? "px-6 py-4 text-sm text-gray-100" : "px-6 py-4 text-sm text-gray-900"}>
                                    {tx.reason || '-'}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span
                                        className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${{
                                            'bg-red-100 text-red-800': tx.risk_score >= 70,
                                            'bg-yellow-100 text-yellow-800': tx.risk_score >= 40 && tx.risk_score < 70,
                                            'bg-green-100 text-green-800': tx.risk_score < 40
                                        }[true]}`}
                                    >
                                        {tx.risk_score}%
                                    </span>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default TransactionHistory;