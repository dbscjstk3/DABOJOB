import { create } from 'zustand';
import { API_ENDPOINTS } from '../lib/api';

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
      console.log('🔍 사용자 정보 가져오기 시도...');
      console.log('📡 API URL:', API_ENDPOINTS.AUTH.ME);

      const response = await fetch(API_ENDPOINTS.AUTH.ME, {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      console.log('📊 API 응답 상태:', response.status, response.statusText);
      console.log('📋 응답 헤더:', Object.fromEntries(response.headers.entries()));

      if (response.ok) {
        const userData: User = await response.json();
        console.log('✅ 사용자 정보 가져오기 성공:', userData);
        console.log('👤 사용자 정보 상세:', {
          id: userData.id,
          name: userData.name,
          email: userData.email,
          role: userData.role,
          provider: userData.provider,
        });
        set({ isAuthed: true, user: userData });
      } else {
        console.log('❌ 사용자 정보 가져오기 실패:', response.status, response.statusText);

        // 응답 본문도 로그에 포함
        try {
          const errorText = await response.text();
          console.log('📄 에러 응답 본문:', errorText);
        } catch (e) {
          console.log('📄 에러 응답 본문 읽기 실패:', e);
        }

        // 401 에러는 로그인하지 않은 상태이므로 정상적인 상황
        if (response.status === 401) {
          console.log('🔒 인증되지 않은 상태 (정상) - 로그인이 필요합니다');
        } else if (response.status === 403) {
          console.log('🚫 접근 권한이 없습니다');
        } else if (response.status >= 500) {
          console.log('🔥 서버 오류가 발생했습니다');
        }

        set({ isAuthed: false, user: null });
      }
    } catch (error) {
      console.error('💥 사용자 정보 가져오기 중 네트워크 오류:', error);
      console.error('🔍 오류 상세:', {
        name: error instanceof Error ? error.name : 'Unknown',
        message: error instanceof Error ? error.message : String(error),
        stack: error instanceof Error ? error.stack : undefined,
      });
      set({ isAuthed: false, user: null });
    }
  },
}));
