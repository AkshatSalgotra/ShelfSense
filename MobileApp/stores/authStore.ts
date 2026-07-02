import { create } from 'zustand';
import * as SecureStore from 'expo-secure-store';

interface AuthState {
  token: string | null;
  role: string | null;
  shopId: string;
  fullName: string;
  setAuth: (token: string, role: string, shopId: string, fullName: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  role: null,
  shopId: '',
  fullName: '',
  setAuth: (token, role, shopId, fullName) => set({ token, role, shopId, fullName }),
  logout: () => {
    SecureStore.deleteItemAsync('token');
    set({ token: null, role: null, shopId: '', fullName: '' });
  },
}));
