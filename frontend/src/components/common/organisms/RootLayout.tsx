import { Outlet, useLocation, useNavigate } from '@tanstack/react-router';
import { useEffect } from 'react';
import { Header } from './Header';
import { Footer } from './Footer';
import { LoginRequiredModal } from './LoginRequiredModal';
import { DuplicateEmailModal } from './DuplicateEmailModal';
import { useAuthStore } from '../../../stores/useAuthStore';
import { API_ENDPOINTS } from '../../../lib/api';

export function RootLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const isLoginPage = location.pathname === '/login';
  const isAdminPage = location.pathname.startsWith('/admin');
  const { isAuthed, user, logout, fetchUser } = useAuthStore();

  // 앱 시작 시 사용자 정보 가져오기 (한 번만 실행)
  useEffect(() => {
    if (import.meta.env.DEV) {
      console.log('🏁 RootLayout: 앱 시작 시 사용자 정보 가져오기');
      console.log('🌐 현재 경로:', location.pathname);
    }
    fetchUser();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // fetchUser를 의존성에서 제거하여 무한 루프 방지

  // 로그인 후 리다이렉트 처리
  useEffect(() => {
    if (import.meta.env.DEV) {
      console.log('🔄 RootLayout: 인증 상태 변화 감지');
      console.log('📊 현재 상태:', { isAuthed, user: user?.name || 'null' });
    }

    const redirectTo = sessionStorage.getItem('post_login_redirect');
    if (import.meta.env.DEV) {
      console.log('💾 저장된 리다이렉트 URL:', redirectTo);
    }

    if (redirectTo && isAuthed) {
      if (import.meta.env.DEV) {
        console.log('✅ 로그인 완료, 리다이렉트 실행');
        console.log('🎯 리다이렉트 대상:', redirectTo);
      }
      sessionStorage.removeItem('post_login_redirect');
      navigate({ to: redirectTo });
    } else if (isAuthed) {
      if (import.meta.env.DEV) {
        console.log('✅ 로그인 상태 확인됨');
      }
    } else {
      if (import.meta.env.DEV) {
        console.log('🔒 로그인되지 않은 상태');
      }
    }
  }, [isAuthed, navigate, user]);

  const handleSubmitSearch = (query: string) => {
    if (import.meta.env.DEV) {
      console.log('검색 제출:', query);
    }
    // 검색 결과 페이지로 이동
    if (query.trim()) {
      navigate({
        to: '/search',
        search: {
          q: query.trim(),
          page: 1,
        },
      });
    }
  };

  const handleLogin = () => {
    // 로그인 페이지로 이동 (실제 로그인은 OAuth를 통해 처리)
    navigate({ to: '/login' });
  };

  const handleLogout = async () => {
    try {
      if (import.meta.env.DEV) {
        console.log('로그아웃 요청 전송:', API_ENDPOINTS.AUTH.LOGOUT);
      }
      const res = await fetch(API_ENDPOINTS.AUTH.LOGOUT, {
        method: 'POST',
        credentials: 'include',
      });
      if (!res.ok) {
        if (import.meta.env.DEV) {
          console.warn('로그아웃 요청 실패', res.status, res.statusText);
        }
      }
    } catch (e) {
      if (import.meta.env.DEV) {
        console.error('로그아웃 요청 오류', e);
      }
    } finally {
      logout();
      navigate({ to: '/' });
    }
  };

  // 관리자 페이지는 Header/Footer 없이 렌더링
  if (isAdminPage) {
    return <Outlet />;
  }

  return (
    <div className="min-h-screen flex flex-col">
      {!isLoginPage && (
        <Header
          user={user ? { name: user.name, role: user.role } : null}
          onLogin={handleLogin}
          onLogout={handleLogout}
          onSubmitSearch={handleSubmitSearch}
        />
      )}
      <main className="w-full flex-1 flex flex-col items-center">
        <Outlet />
      </main>
      {!isLoginPage && <Footer></Footer>}

      {/* 로그인 필요 모달 */}
      <LoginRequiredModal />

      {/* 이메일 중복 모달 */}
      <DuplicateEmailModal />
    </div>
  );
}
