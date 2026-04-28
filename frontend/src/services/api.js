import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const authService = {
  getLoginUrl: async () => {
    const response = await api.get('/auth/login');
    return response.data;
  },
  
  getUser: async (email) => {
    const response = await api.get(`/auth/user/${email}`);
    return response.data;
  },
};

export const chatService = {
  sendMessage: async (message, userEmail) => {
    const response = await api.post('/chat/message', {
      message,
      user_id: userEmail,
    });
    return response.data;
  },
};