import React from 'react';
import { createRouter, createRootRoute, createRoute, useNavigate } from '@tanstack/react-router';
import LoginPage from './pages/LoginPage';
import CalendarPage from './pages/CalendarPage';
import CalendarDetailPage from './pages/CalendarDetailPage';
import SearchDetailPage from './pages/SearchDetailPage';
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
  // beforeLoad: ({ location }) => {
  //   const authed = useAuthStore.getState().isAuthed;
  //   if (!authed) {
  //     throw redirect({ to: '/login', search: { redirect: location.href } });
  //   }
  // },
  component: CalendarDetailPage,
  validateSearch: (search: Record<string, unknown>) => {
    return {
      jobPostingId: (search.jobPostingId as string) || undefined,
    };
  },
});

const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/login',
  component: function LoginRoute() {
    return <LoginPage />;
  },
});

const searchDetailRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/search',
  component: SearchDetailPage,
  validateSearch: (search: Record<string, unknown>) => {
    return {
      q: (search.q as string) || '',
      page: Number(search.page || 1),
    };
  },
});

const authCallbackRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/auth/callback',
  component: function AuthCallback() {
    const navigate = useNavigate();
    const { fetchUser } = useAuthStore.getState();

    React.useEffect(() => {
      const handleAuthCallback = async () => {
        try {
          const urlParams = new URLSearchParams(window.location.search);
          const success = urlParams.get('success');
          const error = urlParams.get('error');

          if (error) {
            console.error('❌ OAuth 인증 오류:', error);
            navigate({ to: '/login' });
            return;
          }

          if (success === 'true') {
            console.log('✅ OAuth 인증 성공');
            await fetchUser();

            // 즉시 리다이렉트 (setTimeout 제거)
            const redirectUrl = sessionStorage.getItem('post_login_redirect') || '/';
            sessionStorage.removeItem('post_login_redirect');
            navigate({ to: redirectUrl });
          } else {
            console.log('❓ OAuth 인증 결과 불명확');
            navigate({ to: '/login' });
          }
        } catch (error) {
          console.error('💥 인증 콜백 처리 중 오류:', error);
          navigate({ to: '/login' });
        }
      };

      handleAuthCallback();
    }, [navigate, fetchUser]);

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
  searchDetailRoute,
  loginRoute,
  authCallbackRoute,
]);

export const router = createRouter({ routeTree });

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}
