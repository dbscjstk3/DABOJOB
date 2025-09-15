// API 관련 상수 및 유틸리티 함수
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://j13a402.p.ssafy.io';

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: (provider: string) => `${API_BASE_URL}/api/auth/login/${provider}`,
    ME: `${API_BASE_URL}/api/auth/me`,
    REFRESH: `${API_BASE_URL}/api/auth/refresh`,
    LOGOUT: `${API_BASE_URL}/api/auth/logout`,
  },
} as const;
