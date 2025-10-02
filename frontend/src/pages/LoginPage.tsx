import { Link } from '@tanstack/react-router';
import { Button } from '../components/common/atoms/Button';
import { Typography } from '../components/common/atoms/Typography';
import { API_ENDPOINTS } from '../lib/api';
import DABOJOB_LOGO_FINAL from '../assets/logo/DABOJOB_LOGO_FINAL.png?format=webp&quality=80';
import SSAFY_logo from '../assets/logo/ssafyLogo.png?format=webp&quality=80';
import GOOGLE_logo from '../assets/logo/googleLogo.svg';
import mascot from '../assets/img/daboja_mascot.png?format=webp&quality=80';

export default function LoginPage() {
  return (
    <div className="flex-1 w-full bg-gradient-to-br from-blue-50 via-slate-50 to-indigo-100 flex items-center justify-center px-4 relative">
      {/* 배경 장식 요소들 */}
      <div className="absolute top-20 left-10 w-20 h-20 bg-blue-200/30 rounded-full blur-xl"></div>
      <div className="absolute bottom-20 right-10 w-32 h-32 bg-indigo-200/30 rounded-full blur-xl"></div>
      <div className="absolute top-1/2 left-1/4 w-16 h-16 bg-purple-200/30 rounded-full blur-lg"></div>

      <div className="mx-auto grid max-w-5xl grid-cols-1 overflow-hidden rounded-3xl bg-white shadow-2xl md:grid-cols-2 h-auto md:h-[600px] w-full animate-in fade-in slide-in-from-bottom-3 duration-300 relative z-10">
        {/* 모바일용 상단 비주얼 영역 */}
        <div className="relative block md:hidden h-56">
          <img
            src={mascot}
            alt="daboja mascot"
            className="h-full w-full object-cover"
            loading="lazy"
          />
          <div className="absolute inset-0 bg-slate-900/20" />
          <div className="absolute bottom-4 left-4 right-4 text-white text-center">
            <Typography as="div" variant="subtitle" weight="semibold" color="white">
              모든 채용 공고를 한 눈에
            </Typography>
            <Typography variant="default" color="white" className="text-white/80 mt-1">
              AI 기반 기업 분석 서비스
            </Typography>
          </div>
        </div>

        {/* 좌측 비주얼 영역 (데스크톱) */}
        <div className="relative hidden md:block overflow-hidden">
          <img src={mascot} alt="daboja mascot" className="h-full w-full object-cover" />

          <div className="absolute inset-0 bg-slate-900/20" />
          <div className="absolute bottom-6 left-6 right-6 text-white">
            <Typography as="div" variant="subtitle" weight="semibold" color="white">
              모든 채용 공고를 한 눈에
            </Typography>
            <Typography variant="default" color="white" className="text-white/80 mt-1">
              AI 기반 기업 분석 서비스
            </Typography>
          </div>
        </div>

        {/* 우측 액션 영역 */}
        <div className="p-8 md:p-12 flex flex-col justify-center">
          <div className="flex items-center gap-2">
            <Link to="/" className="hover:opacity-80 transition-opacity">
              <img src={DABOJOB_LOGO_FINAL} alt="DABOJOB" className="h-10 w-auto" />
            </Link>
          </div>
          <Typography variant="default" color="gray" className="mt-2 mb-8">
            소셜 계정으로 간편하게 로그인하세요.
          </Typography>

          <div className="grid gap-5">
            <Button
              variant="outlined"
              size="lg"
              startIcon={<img src={GOOGLE_logo} alt="GOOGLE" className="h-6 w-6" />}
              onClick={() => (window.location.href = API_ENDPOINTS.AUTH.LOGIN('google'))}
              className="w-full justify-center h-12 border-gray-300 shadow-md hover:shadow-lg transition-all duration-200 hover:scale-[1.02]"
            >
              <Typography variant="default" weight="semibold" className="text-base">
                Google 로그인
              </Typography>
            </Button>

            <Button
              variant="outlined"
              size="lg"
              startIcon={<img src={SSAFY_logo} alt="SSAFY" className="h-6 w-6" />}
              onClick={() => (window.location.href = API_ENDPOINTS.AUTH.LOGIN('ssafy'))}
              className="w-full justify-center h-12 border-gray-300 shadow-md hover:shadow-lg transition-all duration-200 hover:scale-[1.02]"
            >
              <Typography variant="default" weight="semibold" className="text-base">
                SSAFY 로그인
              </Typography>
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
