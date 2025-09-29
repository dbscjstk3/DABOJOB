import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { imagetools } from 'vite-imagetools';
import path from 'path';

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    imagetools({
      // GIF 제외 (SVG는 기본적으로 포함 안됨)
      include: /^[^?]+\.(heif|avif|jpeg|jpg|png|tiff|webp)(\?.*)?$/,
      defaultDirectives: () => {
        return new URLSearchParams({
          format: 'webp',
          quality: '80',
        });
      },
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
