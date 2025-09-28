import { create } from 'zustand';

interface ModalStore {
  // 로그인 모달 상태
  showLoginModal: boolean;
  redirectPath: string | null;
  modalMessage: string;

  // 이메일 중복 모달 상태
  showDuplicateEmailModal: boolean;
  duplicateEmailMessage: string;

  // 로그인 모달 액션
  openLoginModal: (path: string, message?: string) => void;
  closeLoginModal: () => void;
  clearModal: () => void;

  // 이메일 중복 모달 액션
  openDuplicateEmailModal: (message?: string) => void;
  closeDuplicateEmailModal: () => void;
}

export const useModalStore = create<ModalStore>((set) => ({
  // 로그인 모달 초기 상태
  showLoginModal: false,
  redirectPath: null,
  modalMessage: '',

  // 이메일 중복 모달 초기 상태
  showDuplicateEmailModal: false,
  duplicateEmailMessage: '',

  // 로그인 모달 열기
  openLoginModal: (path: string, message: string = '로그인이 필요합니다') => {
    set({
      showLoginModal: true,
      redirectPath: path,
      modalMessage: message,
    });
  },

  // 로그인 모달 닫기 (상태는 유지)
  closeLoginModal: () => {
    set({ showLoginModal: false });
  },

  // 로그인 모달 완전 초기화
  clearModal: () => {
    set({
      showLoginModal: false,
      redirectPath: null,
      modalMessage: '',
    });
  },

  // 이메일 중복 모달 열기
  openDuplicateEmailModal: (message: string = '이미 존재하는 이메일입니다') => {
    set({
      showDuplicateEmailModal: true,
      duplicateEmailMessage: message,
    });
  },

  // 이메일 중복 모달 닫기
  closeDuplicateEmailModal: () => {
    set({
      showDuplicateEmailModal: false,
      duplicateEmailMessage: '',
    });
  },
}));
