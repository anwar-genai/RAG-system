import axios from 'axios';
import { API_BASE_URL } from '../config';

export const authService = {
  async register(username, password) {
    await axios.post(`${API_BASE_URL}/auth/register/`, { username, password });
  },

  async login(username, password) {
    const response = await axios.post(`${API_BASE_URL}/auth/token/`, { username, password });
    localStorage.setItem('access_token', response.data.access);
    localStorage.setItem('refresh_token', response.data.refresh);
    // Fetch and cache user profile
    await this._fetchAndCacheMe();
    return response.data;
  },

  async logout() {
    const refresh = this.getRefreshToken();
    if (refresh) {
      try {
        await axios.post(
          `${API_BASE_URL}/auth/logout/`,
          { refresh },
          { headers: { Authorization: `Bearer ${this.getAccessToken()}` } },
        );
      } catch {
        // Ignore errors — tokens are cleared regardless
      }
    }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_profile');
    // Prevent a different user signing in on this browser from inheriting the previous
    // user's chat session id (which their account wouldn't own anyway, but breaks UX).
    localStorage.removeItem('chat_session_id');
  },

  async _fetchAndCacheMe() {
    try {
      const res = await axios.get(`${API_BASE_URL}/auth/me/`, {
        headers: { Authorization: `Bearer ${this.getAccessToken()}` },
      });
      localStorage.setItem('user_profile', JSON.stringify(res.data));
      return res.data;
    } catch {
      return null;
    }
  },

  getAccessToken() {
    return localStorage.getItem('access_token');
  },

  getRefreshToken() {
    return localStorage.getItem('refresh_token');
  },

  setAccessToken(token) {
    localStorage.setItem('access_token', token);
  },

  isLoggedIn() {
    return !!localStorage.getItem('access_token');
  },

  getUser() {
    const raw = localStorage.getItem('user_profile');
    if (!raw) return null;
    try { return JSON.parse(raw); } catch { return null; }
  },

  isAdmin() {
    return this.getUser()?.role === 'admin';
  },
};

export default authService;
