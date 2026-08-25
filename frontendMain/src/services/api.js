import axios from 'axios';

// API base URL - can be configured via environment variable
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance with default configuration
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60 second timeout for LLM responses
});

// Add request interceptor for logging
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor with enhanced logging
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Generate unique session ID and persist in sessionStorage
const getSessionId = () => {
  let sessionId = sessionStorage.getItem('chat_session_id');
  if (!sessionId) {
    sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    sessionStorage.setItem('chat_session_id', sessionId);
  }
  return sessionId;
};

// Chat API service
export const chatService = {
  /**
   * Send a message to the chat API
   * @param {string} question - User's question
   * @param {string|null} userId - Optional user identifier
   * @returns {Promise<Object>} API response with answer, sources, and top_sources_formatted
   */
  sendMessage: async (question, userId = 'anonymous') => {
    try {
      const payload = {
        question: question,              // Backend expects 'question'
        conversation_id: getSessionId(), // Backend expects 'conversation_id'
        user_id: userId,                 // Backend expects 'user_id'
      };

      const response = await api.post('/api/chat', payload);

      const result = {
        answer: response.data.answer || '',
        sources: response.data.sources || [],
        top_sources_formatted: response.data.top_sources_formatted || '',
        type: response.data.type || 'rag',
        error: response.data.error || null,
      };

      return result;
    } catch (error) {
      // Provide user-friendly error messages
      if (error.response) {
        // Server responded with error status (4xx, 5xx)
        const errorMessage = error.response.data.detail || 
                            error.response.data.message || 
                            'An error occurred while processing your request.';
        throw new Error(errorMessage);
      } else if (error.request) {
        // Request was made but no response received
        throw new Error('No response from server. Please check your connection and try again.');
      } else {
        // Something else happened in setting up the request
        throw new Error('Failed to send message. Please try again.');
      }
    }
  },

  /**
   * Clear the current session
   * @returns {Promise<Object>} Success status
   */
  clearSession: async () => {
    try {
      const sessionId = getSessionId();
      
      await api.post(`/api/session/${sessionId}/clear`);
      
      // Remove session from storage
      sessionStorage.removeItem('chat_session_id');
      
      return { success: true, message: 'Session cleared successfully' };
    } catch (error) {
      // Still remove local session even if API fails
      sessionStorage.removeItem('chat_session_id');
      
      throw new Error('Failed to clear session on server, but local session was cleared.');
    }
  },

  /**
   * Get session statistics
   * @returns {Promise<Object>} Session stats including message count, created_at, etc.
   */
  getSessionStats: async () => {
    try {
      const sessionId = getSessionId();
      const response = await api.get(`/api/session/${sessionId}/stats`);
      return response.data;
    } catch (error) {
      throw new Error('Failed to retrieve session statistics.');
    }
  },

  /**
   * Get current session ID
   * @returns {string} Current session ID
   */
  getCurrentSessionId: () => {
    const sessionId = getSessionId();
    return sessionId;
  },

  /**
   * Create a new session (useful for "New Chat" button)
   * @returns {string} New session ID
   */
  createNewSession: () => {
    sessionStorage.removeItem('chat_session_id');
    const newSessionId = getSessionId();
    return newSessionId;
  },

  /**
   * Health check endpoint
   * @returns {Promise<Object>} Server health status
   */
  healthCheck: async () => {
    try {
      const response = await api.get('/health');
      return response.data;
    } catch (error) {
      throw new Error('Server health check failed.');
    }
  },
};

export default chatService;