import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      // 프론트에서 /api/* 요청을 백엔드로 프록시
      '/api': {
        target: 'http://j13a402.p.ssafy.io',
        changeOrigin: true,
        secure: false,
        ws: false,
      },
    },
  },
});
