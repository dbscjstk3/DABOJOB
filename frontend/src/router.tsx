import React from 'react';
import {
  createRouter,
  createRootRoute,
  createRoute,
  redirect,
  useNavigate,
} from '@tanstack/react-router';
import LoginPage from './pages/LoginPage';
import CalendarPage from './pages/CalendarPage';
import CalendarDetailPage from './pages/CalendarDetailPage';
import SearchDetailPage from './pages/SearchDetailPage';
import NotFoundPage from './pages/NotFoundPage';
import { AdminMappingPage } from './pages/AdminMappingPage';
import AdminCompletedPage from './pages/AdminCompletedPage';
import { useAuthStore } from './stores/useAuthStore';
import { RootLayout } from './components/common/organisms/RootLayout';
import AdminCalendarPage from './pages/AdminCalendarPage';
import { useModalStore } from './stores/useModalStore';

// Admin 라우트용 공통 인증 체크 함수
const checkAdminAuth = async () => {
  // 사용자 정보가 없으면 먼저 가져오기
  const { user, fetchUser } = useAuthStore.getState();
  if (!user) {
    await fetchUser();
  }

  // 다시 한번 확인
  const currentUser = useAuthStore.getState().user;
  const role = currentUser?.role;
  if (!(role === 'admin' || role === 'ROLE_ADMIN')) {
    throw redirect({ to: '/' });
  }
};

const rootRoute = createRootRoute({
  component: RootLayout,
  notFoundComponent: NotFoundPage,
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
  // beforeLoad: async ({ location }) => {
  //   const { isAuthed, fetchUser } = useAuthStore.getState();

  //   // 인증 상태가 없으면 먼저 사용자 정보를 가져와서 확인
  //   if (!isAuthed) {
  //     await fetchUser();
  //     const currentAuthState = useAuthStore.getState().isAuthed;

  //     if (!currentAuthState) {
  //       // 모달 열고 홈으로 리다이렉트
  //       useModalStore
  //         .getState()
  //         .openLoginModal(location.href, '캘린더 상세 정보를 확인하려면 로그인 해주세요');
  //       throw redirect({ to: '/' });
  //     }
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
  beforeLoad: async ({ location }) => {
    const { isAuthed, fetchUser } = useAuthStore.getState();

    // 인증 상태가 없으면 먼저 사용자 정보를 가져와서 확인
    if (!isAuthed) {
      await fetchUser();
      const currentAuthState = useAuthStore.getState().isAuthed;

      if (!currentAuthState) {
        // 모달 열고 홈으로 리다이렉트
        useModalStore
          .getState()
          .openLoginModal(location.href, '검색 결과를 확인하려면 로그인 해주세요!');
        throw redirect({ to: '/' });
      }
    }
  },
  component: SearchDetailPage,
  validateSearch: (search: Record<string, unknown>) => {
    return {
      q: (search.q as string) || '',
      page: Number(search.page || 1),
    };
  },
});

// Admin calendar route - same UI, role/데이터는 컴포넌트 내부에서 분기
const adminCalendarRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/admin',
  beforeLoad: checkAdminAuth,
  component: AdminCalendarPage,
});

// Admin routes - IP 화이트리스트로 서버에서 접근 제어
const adminMappingRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/admin/mapping/$companyId',
  beforeLoad: checkAdminAuth,
  component: AdminMappingPage,
});

const adminJobCompletedRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/admin/jobs/$jobId/complete',
  beforeLoad: checkAdminAuth,
  component: AdminCompletedPage,
  validateSearch: (search: Record<string, unknown>) => {
    return {
      companyId: (search.companyId as string) || undefined,
      mappingId: (search.mappingId as string) || undefined,
    };
  },
});

const authCallbackRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/auth/callback',
  component: function AuthCallback() {
    const navigate = useNavigate();
    const { fetchUser } = useAuthStore.getState();
    const { openDuplicateEmailModal } = useModalStore.getState();

    React.useEffect(() => {
      const handleAuthCallback = async () => {
        try {
          const urlParams = new URLSearchParams(window.location.search);
          const success = urlParams.get('success');
          const error = urlParams.get('error');

          if (error) {
            console.error('❌ OAuth 인증 오류:', error);

            // 이메일 중복 에러 처리
            if (
              error === 'duplicate_email' ||
              error.includes('duplicate') ||
              error.includes('exists')
            ) {
              openDuplicateEmailModal('이미 존재하는 이메일입니다. 다른 계정으로 로그인해 주세요.');
              navigate({ to: '/' });
              return;
            }

            // 기타 에러는 로그인 페이지로
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
    }, [navigate, fetchUser, openDuplicateEmailModal]);

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
  adminCalendarRoute,
  adminMappingRoute,
  adminJobCompletedRoute,
  loginRoute,
  authCallbackRoute,
]);

export const router = createRouter({ routeTree });

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}
