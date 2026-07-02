import axios from "axios";
import * as SecureStore from "expo-secure-store";

const api = axios.create({ 
  baseURL: process.env.EXPO_PUBLIC_API_URL || "http://localhost:8000" 
});

// Attach token to every request
api.interceptors.request.use(async (config) => {
  const token = await SecureStore.getItemAsync("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-logout on 401
api.interceptors.response.use(
  (res) => res,
  async (err) => {
    if (err.response?.status === 401) {
      await SecureStore.deleteItemAsync("token");
      // we'll handle the navigation in the component or auth store side
    }
    return Promise.reject(err);
  }
);

export default api;
