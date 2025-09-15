import { useEffect, useState } from 'react';
import { Button } from '../components/common/atoms/Button';
import { cn } from '../lib/utils';
import DABOJOBLogo from '../assets/logo/DABOJOB_logo.svg';
import GoogleLogo from '../assets/logo/googleLogo.svg';
import SSAFYLogo from '../assets/logo/ssafyLogo.png';
import Cactus from '../assets/img/cactus.svg';
import Woman from '../assets/img/woman.svg';

type LoginPageProps = {
  redirectTo?: string;
};

export default function LoginPage({ redirectTo: _redirectTo }: LoginPageProps) {
  // 디자인 기준 사이즈(카드): 1366 x 849
  const BASE_WIDTH = 1366;
  const BASE_HEIGHT = 849;
  const [scale, setScale] = useState(1);

  useEffect(() => {
    const computeScale = () => {
      const margin = 24; // 좌우/상하 여백
      const availableW = window.innerWidth - margin * 2;
      const availableH = window.innerHeight - margin * 2;
      const scaleW = availableW / BASE_WIDTH;
      const scaleH = availableH / BASE_HEIGHT;
      const next = Math.min(scaleW, scaleH, 1); // 1배 초과로 커지지 않도록 제한
      setScale(next);
    };
    computeScale();
    window.addEventListener('resize', computeScale);
    return () => window.removeEventListener('resize', computeScale);
  }, []);
  const handleSSAFYLogin = () => {
    // 실제 로그인 로직 (현재는 시뮬레이션)
    // 실제 구현 시 아래 코드 사용
    if (_redirectTo) {
      sessionStorage.setItem('post_login_redirect', _redirectTo);
    }
    window.location.href = 'http://j13a402.p.ssafy.io/api/auth/login/ssafy';
  };

  const handleGoogleLogin = () => {
    // 실제 로그인 로직 (현재는 시뮬레이션)
    // 실제 구현 시 아래 코드 사용
    if (_redirectTo) {
      sessionStorage.setItem('post_login_redirect', _redirectTo);
    }
    window.location.href = 'http://j13a402.p.ssafy.io/api/auth/login/google';
  };

  return (
    <div className={cn('min-h-screen w-full flex items-center justify-center p-4', 'bg-white')}>
      {/* 스케일 래퍼: 스케일 적용 후도 가운데 정렬 유지 */}
      <div style={{ width: BASE_WIDTH * scale, height: BASE_HEIGHT * scale }}>
        {/* 메인 카드 */}
        <div
          className="relative w-[1366px] h-[849px] rounded-[40px] bg-white shadow-[4px_4px_70px_rgba(0,0,0,0.1)] overflow-hidden"
          style={{ transform: `scale(${scale})`, transformOrigin: 'top left' }}
        >
          {/* 우측 컬러 패널 */}
          <div className="absolute top-0 right-0 h-full w-[489px] bg-[#C0DBEA] rounded-[40px]" />

          {/* 상단 로고 */}
          <div className="absolute left-[100px] top-[100px] z-10">
            <img src={DABOJOBLogo} alt="DABOJOB" className="h-[74px] w-auto" />
          </div>

          {/* 일러스트 - woman */}
          <img
            src={Woman}
            alt="woman"
            className="absolute left-[600px] top-[279px] h-[703px] w-auto pointer-events-none select-none z-10"
          />

          {/* 싸피 로그인 버튼 */}
          <div className="absolute left-[130px] top-[400px] w-[472px] h-[100px] z-10">
            <Button
              onClick={handleSSAFYLogin}
              startIcon={
                <img src={SSAFYLogo} alt="SSAFY" className="h-[47px] w-[66px] object-contain" />
              }
              className={cn(
                'w-full h-full rounded-[21px] bg-white shadow-[0_38.49px_71.48px_rgba(0,0,0,0.07)]',
                'flex items-center gap-[31.5px] pl-[31.5px] pr-[31.5px] justify-center border border-gray-200',
              )}
            >
              <span className="text-[32px] leading-[38px] font-medium text-black/60">
                싸피 로그인
              </span>
            </Button>
          </div>

          {/* 구글 로그인 버튼 */}
          <div className="absolute left-[130px] top-[530px] w-[472px] h-[100px] z-10">
            <Button
              onClick={handleGoogleLogin}
              startIcon={<img src={GoogleLogo} alt="Google" className="h-[50px] w-[50px]" />}
              className={cn(
                'w-full h-full rounded-[21px] bg-white shadow-[0_38.49px_71.48px_rgba(0,0,0,0.07)]',
                'flex items-center gap-[31.5px] pl-[31.5px] pr-[31.5px] justify-center border border-gray-200',
              )}
            >
              <span className="text-[32px] leading-[38px] font-medium text-black/60">
                구글 로그인
              </span>
            </Button>
          </div>

          {/* 선인장 일러스트 */}
          <img
            src={Cactus}
            alt="cactus"
            className="absolute right-[60px] bottom-0 h-[550px] w-auto pointer-events-none select-none z-0"
          />
        </div>
      </div>
    </div>
  );
}
