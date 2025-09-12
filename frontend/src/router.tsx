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
    // 백엔드 OAuth 성공 시 쿠키에 토큰이 설정되어 있음. 클라이언트 상태만 동기화.
    useAuthStore.getState().login();
    const stored = sessionStorage.getItem('post_login_redirect');
    const target = stored || '/';
    if (stored) sessionStorage.removeItem('post_login_redirect');
    navigate({ to: target });
    return <div className="p-8">로그인 처리중...</div>;
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
