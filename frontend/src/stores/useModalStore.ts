import { create } from 'zustand';

interface ModalStore {
  // 상태
  showLoginModal: boolean;
  redirectPath: string | null;
  modalMessage: string;

  // 액션
  openLoginModal: (path: string, message?: string) => void;
  closeLoginModal: () => void;
  clearModal: () => void;
}

export const useModalStore = create<ModalStore>((set) => ({
  // 초기 상태
  showLoginModal: false,
  redirectPath: null,
  modalMessage: '',

  // 모달 열기
  openLoginModal: (path: string, message: string = '로그인이 필요합니다') => {
    set({
      showLoginModal: true,
      redirectPath: path,
      modalMessage: message,
    });
  },

  // 모달 닫기 (상태는 유지)
  closeLoginModal: () => {
    set({ showLoginModal: false });
  },

  // 모달 완전 초기화
  clearModal: () => {
    set({
      showLoginModal: false,
      redirectPath: null,
      modalMessage: '',
    });
  },
}));
