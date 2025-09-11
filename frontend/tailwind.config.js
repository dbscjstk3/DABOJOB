/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{html,js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        daboja: {
          default: '#099AEE',
          tag: '#E3E3E3',
          gray: {
            light: '#F1F5F9', // slate-100과 동일
            default: '#F1F5F9', // 기본 회색
            dark: '#E2E8F0', // slate-200과 동일
          },
        },
      },
      fontFamily: {
        pretendard: ['Pretendard', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
