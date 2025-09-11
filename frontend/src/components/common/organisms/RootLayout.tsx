import { Outlet } from '@tanstack/react-router';
import { Header } from './Header';
import type { SearchItem } from '../molecules/SearchResult';
import { Footer } from './Footer';

export function RootLayout() {
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

  return (
    <div className="min-h-screen flex flex-col">
      <Header
        fetchSuggestions={fetchSuggestions}
        onSelectSuggestion={handleSelectSuggestion}
        onSubmitSearch={handleSubmitSearch}
        // user={null} // 로그인 전
        // user={{ name: '홍길동' }} // 로그인 후 테스트용
      />
      <main className="w-full flex-1">
        <Outlet />
      </main>
      <Footer></Footer>
    </div>
  );
}
