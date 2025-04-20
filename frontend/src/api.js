import axios from 'axios';
import { getRefreshToken, saveAccessToken, clearTokens } from './utils/auth';

const api = axios.create({
  baseURL: 'http://10.88.20.216:8000/api', //
});

api.interceptors.response.use(
  res => res,
  async error => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refresh = getRefreshToken();
      if (refresh) {
        try {
          const res = await axios.post('http://10.88.20.216:8000/api/auth/token/refresh/', { refresh });
          saveAccessToken(res.data.access);
          originalRequest.headers['Authorization'] = `Bearer ${res.data.access}`;
          return axios(originalRequest);
        } catch (refreshError) {
          clearTokens();
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

api.interceptors.request.use(config => {
  const token = localStorage.getItem('access');
  if (token) config.headers['Authorization'] = `Bearer ${token}`;
  return config;
});

export default api;
