import axios, { AxiosInstance } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Create axios instance with increased timeout for slow browser automation operations
const api: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 300000, // 5 minutes timeout for slow browser automation
});

// Add token to requests if available
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Handle 401 errors (unauthorized) and timeout errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    // Handle timeout errors
    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      error.response = {
        ...error.response,
        data: {
          detail: 'Request timed out. The operation may still be processing. Please try again in a moment.',
        },
      };
    }
    // Handle browser navigation errors with more helpful message
    const errorDetail = error.response?.data?.detail || '';
    if (errorDetail.includes('Failed to navigate') || errorDetail.includes('ERR_ABORTED')) {
      error.response = {
        ...error.response,
        data: {
          detail: 'Browser is still navigating to the notebook. Please wait a moment and try again, or refresh the page.',
        },
      };
    }
    return Promise.reject(error);
  }
);

export default api;

