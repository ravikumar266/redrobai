import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to automatically add Bearer token to requests
api.interceptors.request.use(async (config) => {
  let token = localStorage.getItem('access_token');
  
  if (!token) {
    try {
      const formData = new URLSearchParams();
      formData.append('username', 'testuser');
      formData.append('password', 'password');
      
      const response = await axios.post(`${config.baseURL}/token`, formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });
      token = response.data.access_token;
      localStorage.setItem('access_token', token);
    } catch (error) {
      console.error('Failed to get auth token:', error);
    }
  }

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

export default api;
