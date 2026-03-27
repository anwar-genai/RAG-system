import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const chatService = {
  /**
   * Send a message to the chat API
   * @param {string} userMessage - The user's message
   * @param {string} sessionId - Optional session ID
   * @returns {Promise} Response with answer, sources, and session_id
   */
  sendMessage: async (userMessage, sessionId = null) => {
    try {
      const payload = {
        user_message: userMessage,
      };

      if (sessionId) {
        payload.session_id = sessionId;
      }

      const response = await apiClient.post('chat/', payload);
      return response.data;
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  },

  /**
   * Get chat session with all messages
   * @param {string} sessionId - The session ID
   * @returns {Promise} Session data with messages
   */
  getSession: async (sessionId) => {
    try {
      const response = await apiClient.get(`session/${sessionId}/`);
      return response.data;
    } catch (error) {
      console.error('Error fetching session:', error);
      throw error;
    }
  },

  /**
   * Create a new chat session
   * @returns {Promise} New session data with session_id
   */
  createSession: async () => {
    try {
      const response = await apiClient.post('session/');
      return response.data;
    } catch (error) {
      console.error('Error creating session:', error);
      throw error;
    }
  },

  /**
   * Send a message and stream the assistant reply (SSE).
   * @param {string} userMessage
   * @param {string} sessionId
   * @param {{ onChunk: (text: string) => void, onDone: (data: { sources: string[], message_id: number }) => void }} callbacks
   */
  sendMessageStream: async (userMessage, sessionId, { onChunk, onDone }) => {
    const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
    const res = await fetch(`${baseURL}/chat/stream/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
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
