import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export const authService = {
  async login(username, password) {
    const response = await axios.post(`${API_BASE_URL}/auth/token/`, { username, password });
    localStorage.setItem('access_token', response.data.access);
    localStorage.setItem('refresh_token', response.data.refresh);
    return response.data;
  },

  async logout() {
    const refresh = localStorage.getItem('refresh_token');
    if (refresh) {
      try {
        await axios.post(
          `${API_BASE_URL}/auth/logout/`,
          { refresh },
          { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` } },
        );
      } catch {
        // Ignore errors — tokens are cleared regardless
      }
    }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },

  getAccessToken() {
    return localStorage.getItem('access_token');
  },

  getRefreshToken() {
    return localStorage.getItem('refresh_token');
  },

  isLoggedIn() {
    return !!localStorage.getItem('access_token');
  },

  setAccessToken(token) {
    localStorage.setItem('access_token', token);
  },
};

export default authService;
