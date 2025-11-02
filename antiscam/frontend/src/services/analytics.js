import api from './api';

// Get user analytics data
export const getUserAnalytics = async () => {
    try {
        const response = await api.get('/api/user-analytics');
        return response.data;
    } catch (error) {
        console.error('Error fetching user analytics:', error);
        throw error;
    }
};

// Get global analytics data
export const getGlobalAnalytics = async () => {
    try {
        const response = await api.get('/api/global-analytics');
        return response.data;
    } catch (error) {
        console.error('Error fetching global analytics:', error);
        throw error;
    }
};

export default {
    getUserAnalytics,
    getGlobalAnalytics
};