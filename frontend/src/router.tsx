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
    const navigate = useNavigate();
    const { redirect: backTo } = useSearch({ from: '/login' }) as { redirect?: string };
    return (
      <LoginPage
        onSubmit={() => {
          useAuthStore.getState().login();
          navigate({ to: backTo ?? '/' });
        }}
      />
    );
  },
});

const routeTree = rootRoute.addChildren([calendarListRoute, calendarDetailRoute, loginRoute]);

export const router = createRouter({ routeTree });

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}
