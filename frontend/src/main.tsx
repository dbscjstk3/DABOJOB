import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App.tsx';

// MSW 초기화 함수
async function enableMocking() {
  // 환경변수로 MSW 사용 여부 확인
  if (import.meta.env.VITE_USE_MSW !== 'true') {
    console.log('🔌 Using real API');
    return;
  }

  console.log('🎭 MSW enabled - Using mock API');

  const { worker } = await import('./mocks/browser');

  // MSW 시작
  return worker.start({
    onUnhandledRequest: 'bypass',
    serviceWorker: {
      url: '/mockServiceWorker.js',
    },
  });
}

// MSW 초기화 후 React 앱 마운트
enableMocking().then(() => {
  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <App />
    </StrictMode>,
  );
});
