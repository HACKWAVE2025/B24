import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('figment_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Handle token expiration
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('figment_token');
      localStorage.removeItem('figment_user');
      // Redirect to login page if not already there
      if (window.location.pathname !== '/auth' && window.location.pathname !== '/') {
        window.location.href = '/auth';
      }
    }
    return Promise.reject(error);
  }
);

// Analyze transaction through all agents
export const analyzeTransaction = async (transactionData) => {
  try {
    // Get current time
    const now = new Date();
    const timeStr = now.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });

    // Prepare payload matching backend expectations
    const payload = {
      receiver: transactionData.upiId || transactionData.receiver,
      amount: parseFloat(transactionData.amount),
      reason: transactionData.message || transactionData.reason || '',
      time: transactionData.time || timeStr,
      typing_speed: transactionData.typing_speed || null,
      hesitation_count: transactionData.hesitation_count || null
    };

    const response = await api.post('/api/analyze', payload);
    return response.data;
  } catch (error) {
    console.error('Error analyzing transaction:', error);
    throw error;
  }
};

// Report a scam
export const reportScam = async (reportData) => {
  try {
    const payload = {
      receiver: reportData.receiver || reportData.upiId,
      reason: reportData.reason || 'Reported scam'
    };

    const response = await api.post('/api/report', payload);
    return response.data;
  } catch (error) {
    console.error('Error reporting scam:', error);
    throw error;
  }
};

// Get transaction history
export const getTransactionHistory = async () => {
  try {
    const response = await api.get('/api/history');
    return response.data;
  } catch (error) {
    console.error('Error fetching history:', error);
    throw error;
  }
};

// Complete transaction (after PIN confirmation)
export const completeTransaction = async (transactionData) => {
  try {
    // Remove user_id as it comes from token
    const { user_id, ...payload } = transactionData;
    const response = await api.post('/api/complete-transaction', payload);
    return response.data;
  } catch (error) {
    console.error('Error completing transaction:', error);
    throw error;
  }
};

// Submit feedback after transaction
export const submitFeedback = async (feedbackData) => {
  try {
    // Remove user_id as it comes from token
    const { user_id, ...payload } = feedbackData;
    const response = await api.post('/api/feedback', payload);
    return response.data;
  } catch (error) {
    console.error('Error submitting feedback:', error);
    throw error;
  }
};

export default api;

