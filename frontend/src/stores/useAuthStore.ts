import { create } from 'zustand';

type AuthState = {
  isAuthed: boolean;
  login: () => void;
  logout: () => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  isAuthed: false,
  login: () => set({ isAuthed: true }),
  logout: () => set({ isAuthed: false }),
}));
