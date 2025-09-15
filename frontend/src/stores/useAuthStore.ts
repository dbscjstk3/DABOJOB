import { create } from 'zustand';

type User = {
  id: number;
  name: string;
  email: string;
  role: string;
  provider: string;
};

type AuthState = {
  isAuthed: boolean;
  user: User | null;
  login: (user: User) => void;
  logout: () => void;
  fetchUser: () => Promise<void>;
};

export const useAuthStore = create<AuthState>((set) => ({
  isAuthed: false,
  user: null,
  login: (user: User) => set({ isAuthed: true, user }),
  logout: () => set({ isAuthed: false, user: null }),
  fetchUser: async () => {
    try {
      const response = await fetch('j13a402.p.ssafy.io/api/auth/me', {
        credentials: 'include',
      });

      if (response.ok) {
        const userData: User = await response.json();
        set({ isAuthed: true, user: userData });
      } else {
        set({ isAuthed: false, user: null });
      }
    } catch (error) {
      console.error('Failed to fetch user:', error);
      set({ isAuthed: false, user: null });
    }
  },
}));
