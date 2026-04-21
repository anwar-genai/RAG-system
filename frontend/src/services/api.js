import axios from 'axios';
import authService from './auth';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Inject access token on every request
apiClient.interceptors.request.use((config) => {
  const token = authService.getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// On 401, attempt a silent token refresh then retry once
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refresh = authService.getRefreshToken();
      if (refresh) {
        try {
          const res = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, { refresh });
          authService.setAccessToken(res.data.access);
          original.headers.Authorization = `Bearer ${res.data.access}`;
          return apiClient(original);
        } catch {
          // Refresh failed — clear tokens so the login screen appears
          authService.logout();
          window.location.reload();
        }
      }
    }
    return Promise.reject(error);
  },
);

export const chatService = {
  sendMessage: async (userMessage, sessionId = null) => {
    const payload = { user_message: userMessage };
    if (sessionId) payload.session_id = sessionId;
    const response = await apiClient.post('chat/', payload);
    return response.data;
  },

  getSession: async (sessionId) => {
    const response = await apiClient.get(`session/${sessionId}/`);
    return response.data;
  },

  createSession: async () => {
    const response = await apiClient.post('session/');
    return response.data;
  },

  uploadDocuments: async (files) => {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));
    const response = await apiClient.post('documents/upload/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  sendMessageStream: async (userMessage, sessionId, { onChunk, onDone }) => {
    const res = await fetch(`${API_BASE_URL}/chat/stream/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authService.getAccessToken()}`,
      },
      body: JSON.stringify({
        user_message: userMessage,
        ...(sessionId && { session_id: sessionId }),
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || res.statusText);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split('\n\n');
      buffer = parts.pop() || '';
      for (const part of parts) {
        const line = part.trim();
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.t === 'chunk' && data.content != null) onChunk(data.content);
            else if (data.t === 'done') onDone(data);
            else if (data.t === 'error') throw new Error(data.error);
          } catch (e) {
            if (e instanceof SyntaxError) continue;
            throw e;
          }
        }
      }
    }

    if (buffer.trim()) {
      const line = buffer.trim();
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        if (data.t === 'done') onDone(data);
      }
    }
  },
};

export default chatService;
