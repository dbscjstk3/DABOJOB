import { setupWorker } from 'msw/browser';
import { handlers } from './handlers';

// 브라우저 환경에서 사용하는 MSW worker 설정
export const worker = setupWorker(...handlers);

// 개발 환경에서 사용할 수 있는 MSW 제어 함수들
export const mswController = {
  // MSW 시작
  start: () => {
    return worker.start({
      onUnhandledRequest: 'bypass', // 처리되지 않은 요청은 그대로 통과
      serviceWorker: {
        url: '/mockServiceWorker.js', // public 폴더의 Service Worker 파일
      },
    });
  },

  // MSW 중지
  stop: () => {
    return worker.stop();
  },

  // 핸들러 재설정 (런타임에 변경 가능)
  resetHandlers: () => {
    return worker.resetHandlers(...handlers);
  },

  // 개발용 로그
  log: (message: string) => {
    console.log(`🎭 MSW Controller: ${message}`);
  },
};
