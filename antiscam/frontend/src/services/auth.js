import axios from 'axios';
import api from './api';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

// Token management
export const getToken = () => {
  return localStorage.getItem('figment_token');
};

export const setToken = (token) => {
  localStorage.setItem('figment_token', token);
};

export const removeToken = () => {
  localStorage.removeItem('figment_token');
};

export const getUser = () => {
  const userStr = localStorage.getItem('figment_user');
  return userStr ? JSON.parse(userStr) : null;
};

export const setUser = (user) => {
  localStorage.setItem('figment_user', JSON.stringify(user));
};

export const removeUser = () => {
  localStorage.removeItem('figment_user');
};

// Auth API calls
export const signup = async (name, email, password) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/api/auth/signup`, {
      name,
      email,
      password
    });
    
    if (response.data.success) {
      setToken(response.data.token);
      setUser(response.data.user);
    }
    
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Signup failed' };
  }
};

export const login = async (email, password) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/api/auth/login`, {
      email,
      password
    });
    
    if (response.data.success) {
      setToken(response.data.token);
      setUser(response.data.user);
    }
    
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Login failed' };
  }
};


export const verifyToken = async () => {
  const token = getToken();
  if (!token) return false;
  
  try {
    const response = await axios.post(`${API_BASE_URL}/api/auth/verify`, {
      token
    });
    return response.data.valid === true;
  } catch (error) {
    return false;
  }
};

export const getCurrentUser = async () => {
  const token = getToken();
  if (!token) return null;
  
  try {
    const response = await api.get('/api/auth/me');
    return response.data.user;
  } catch (error) {
    return null;
  }
};

export const logout = () => {
  removeToken();
  removeUser();
};

