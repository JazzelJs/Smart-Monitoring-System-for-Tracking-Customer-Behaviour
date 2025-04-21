import axios from 'axios';
import { getRefreshToken, saveAccessToken, clearTokens } from './utils/auth';

export const API_BASE_URL = 'http://10.10.170.26:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL, //
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
          const res = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, { refresh });
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
