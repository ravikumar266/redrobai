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
    // Let the request fail with 401 if no token, 
    // or we could redirect to /login here.
    // For now, we will let the components handle redirect or use a response interceptor.
  }

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Add response interceptor to handle 401/403
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && (error.response.status === 401 || error.response.status === 403)) {
      // Clear token and redirect to login
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_role');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
