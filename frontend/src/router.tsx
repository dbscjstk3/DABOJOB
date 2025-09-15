import React from 'react';
import {
  createRouter,
  createRootRoute,
  createRoute,
  redirect,
  useNavigate,
  useSearch,
} from '@tanstack/react-router';
import LoginPage from './pages/LoginPage';
import CalendarPage from './pages/CalendarPage';
import CalendarDetailPage from './pages/CalendarDetailPage';
import { useAuthStore } from './stores/useAuthStore';
import { RootLayout } from './components/common/organisms/RootLayout';

const rootRoute = createRootRoute({
  component: RootLayout,
  notFoundComponent: () => <div>404 Not Found</div>,
});

const calendarListRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: CalendarPage,
});

// calendar 상세 페이지는 로그인 이후에만 접속 가능.
const calendarDetailRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/calendar/$id',
  beforeLoad: ({ location }) => {
    const authed = useAuthStore.getState().isAuthed;
    if (!authed) {
      throw redirect({ to: '/login', search: { redirect: location.href } });
    }
  },
  component: CalendarDetailPage,
});

const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/login',
  component: function LoginRoute() {
    const { redirect: backTo } = useSearch({ from: '/login' }) as { redirect?: string };
    return (
      <div className="min-h-screen">
        <LoginPage redirectTo={backTo ?? '/'} />
      </div>
    );
  },
});

const authCallbackRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/auth/callback',
  component: function AuthCallback() {
    const navigate = useNavigate();
    const { fetchUser } = useAuthStore.getState();

    // URL 파라미터 확인
    const urlParams = new URLSearchParams(window.location.search);
    const success = urlParams.get('success');
    const error = urlParams.get('error');

    React.useEffect(() => {
      const handleAuthCallback = async () => {
        try {
          if (error) {
            console.error('OAuth 인증 오류:', error);
            navigate({ to: '/login' });
            return;
          }

          if (success === 'true') {
            console.log('OAuth 인증 성공, 사용자 정보 가져오기 시작');
            // 백엔드에서 쿠키에 토큰을 설정했으므로 사용자 정보 가져오기
            await fetchUser();

            // 잠시 대기 후 리다이렉트 (상태 업데이트 시간 확보)
            setTimeout(() => {
              const stored = sessionStorage.getItem('post_login_redirect');
              const target = stored || '/';
              if (stored) sessionStorage.removeItem('post_login_redirect');
              console.log('리다이렉트 대상:', target);
              navigate({ to: target });
            }, 1000);
          } else {
            console.log('OAuth 인증 결과 불명확, 로그인 페이지로 이동');
            navigate({ to: '/login' });
          }
        } catch (error) {
          console.error('인증 콜백 처리 중 오류:', error);
          navigate({ to: '/login' });
        }
      };

      handleAuthCallback();
    }, [navigate, fetchUser, error, success]);

    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-lg text-gray-600">로그인 처리중...</p>
        </div>
      </div>
    );
  },
});

const routeTree = rootRoute.addChildren([
  calendarListRoute,
  calendarDetailRoute,
  loginRoute,
  authCallbackRoute,
]);

export const router = createRouter({ routeTree });

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}
