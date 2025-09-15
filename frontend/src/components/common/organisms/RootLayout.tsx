import { Outlet, useLocation, useNavigate } from '@tanstack/react-router';
import { useEffect } from 'react';
import { Header } from './Header';
import type { SearchItem } from '../molecules/SearchResult';
import { Footer } from './Footer';
import { useAuthStore } from '../../../stores/useAuthStore';

export function RootLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const isLoginPage = location.pathname === '/login';
  const { isAuthed, user, logout, fetchUser } = useAuthStore();

  // 앱 시작 시 사용자 정보 가져오기
  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  // 로그인 후 리다이렉트 처리
  useEffect(() => {
    const redirectTo = sessionStorage.getItem('post_login_redirect');
    if (redirectTo && isAuthed) {
      sessionStorage.removeItem('post_login_redirect');
      navigate({ to: redirectTo });
    }
  }, [isAuthed, navigate]);

  // 임시 mock fetchSuggestions 함수(추후 실제 api호출로 변경할 예정)
  const fetchSuggestions = async (query: string, signal?: AbortSignal): Promise<SearchItem[]> => {
    // 300ms 지연으로 실제 API 호출 시뮬레이션
    await new Promise((resolve) => setTimeout(resolve, 300));

    // signal이 abort되었는지 확인
    if (signal?.aborted) {
      throw new DOMException('Aborted', 'AbortError');
    }

    // mock 데이터 반환
    const mockData: SearchItem[] = [
      { id: 1, label: `${query} - 삼성전자` },
      { id: 2, label: `${query} - LG전자` },
      { id: 3, label: `${query} - SK하이닉스` },
      { id: 4, label: `${query} - 네이버` },
      { id: 5, label: `${query} - 카카오` },
    ];

    // query를 포함하는 항목만 필터링
    return mockData.filter((item) => item.label.toLowerCase().includes(query.toLowerCase()));
  };

  const handleSelectSuggestion = (item: SearchItem) => {
    console.log('선택된 항목:', item);
    // TODO: 실제 라우팅 또는 검색 처리
  };

  const handleSubmitSearch = (query: string) => {
    console.log('검색 제출:', query);
    // TODO: 검색 결과 페이지로 이동
  };

  const handleLogin = () => {
    // 로그인 페이지로 이동 (실제 로그인은 OAuth를 통해 처리)
    navigate({ to: '/login' });
  };

  const handleLogout = () => {
    logout();
  };

  return (
    <div className="min-h-screen flex flex-col">
      {!isLoginPage && (
        <Header
          user={user ? { name: user.name } : null}
          onLogin={handleLogin}
          onLogout={handleLogout}
          fetchSuggestions={fetchSuggestions}
          onSelectSuggestion={handleSelectSuggestion}
          onSubmitSearch={handleSubmitSearch}
        />
      )}
      <main className="w-full flex-1">
        <Outlet />
      </main>
      {!isLoginPage && <Footer></Footer>}
    </div>
  );
}
