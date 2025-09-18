import { useState, useEffect } from 'react';
import { useSearch, useNavigate } from '@tanstack/react-router';
import SearchResultCard from '@/components/search/organisms/SearchResultCard';
import PaginationControls from '@/components/search/molecules/PaginationControls';
import EmptyState from '@/components/search/molecules/EmptyState';
import Typography from '@/components/common/atoms/Typography';

// 검색 결과 타입 정의
interface SearchResult {
  id: string;
  status: 'started' | 'ended';
  companyName: string;
  title: string;
  experienceLevel: string;
  period: string;
  jobCategory: string;
  url?: string;
}

// 검색 파라미터 타입 정의
interface SearchParams {
  q?: string;
  page?: number;
}

export default function SearchDetailPage() {
  const navigate = useNavigate({ from: '/search' });
  const searchParams = useSearch({ from: '/search' }) as SearchParams;
  const query = searchParams.q || '';
  const currentPage = searchParams.page || 1;

  const [results, setResults] = useState<SearchResult[]>([]);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(false);

  // Mock 데이터 생성 함수 (실제로는 API 호출로 대체)
  // query: string 추가할 예정
  const fetchSearchResults = async (page: number = 1) => {
    // 실제 API 호출 예시:
    // const response = await fetch(`/api/search?q=${query}&page=${page}`);
    // return response.json();

    // Mock 데이터
    const mockResults: SearchResult[] = [
      {
        id: '1',
        status: 'started',
        companyName: '삼성전자',
        title: '2025 하반기 삼성전자 집중 채용 (신입/경력)',
        experienceLevel: '신입',
        period: '09/05~09/12',
        jobCategory: 'IT 직무',
        url: 'https://example.com/1',
      },
      {
        id: '2',
        status: 'ended',
        companyName: '삼성전자',
        title: '2025 상반기 삼성전자 SW 개발자 모집',
        experienceLevel: '경력',
        period: '08/01~08/15',
        jobCategory: '소프트웨어 개발',
        url: 'https://example.com/2',
      },
      {
        id: '3',
        status: 'ended',
        companyName: '삼성전자',
        title: '2025 상반기 삼성전자 SW 개발자 모집',
        experienceLevel: '경력',
        period: '08/01~08/15',
        jobCategory: '소프트웨어 개발',
        url: 'https://example.com/2',
      },
      {
        id: '4',
        status: 'ended',
        companyName: '삼성전자',
        title: '2025 상반기 삼성전자 SW 개발자 모집',
        experienceLevel: '경력',
        period: '08/01~08/15',
        jobCategory: '소프트웨어 개발',
        url: 'https://example.com/2',
      },
      {
        id: '5',
        status: 'ended',
        companyName: '삼성전자',
        title: '2025 상반기 삼성전자 SW 개발자 모집',
        experienceLevel: '경력',
        period: '08/01~08/15',
        jobCategory: '소프트웨어 개발',
        url: 'https://example.com/2',
      },
    ];

    return {
      items: mockResults,
      totalPages: 10,
      currentPage: page,
    };
  };
  // query: string 추가할 예정
  useEffect(() => {
    const loadResults = async () => {
      if (!query) return;

      setLoading(true);
      try {
        const data = await fetchSearchResults(currentPage);
        setResults(data.items);
        setTotalPages(data.totalPages);
      } catch (error) {
        console.error('검색 실패:', error);
      } finally {
        setLoading(false);
      }
    };

    loadResults();
  }, [currentPage, query]);

  // 페이지 변경 핸들러
  const handlePageChange = (newPage: number) => {
    navigate({
      search: (prev) => ({
        ...prev,
        page: newPage,
      }),
    });
  };

  return (
    <div className="max-w-5xl mx-auto p-4 space-y-4">
      <Typography variant="title" weight="bold" className="mt-5">
        {query ? `"${query}" 검색 결과` : '검색'}
      </Typography>

      {!query ? (
        <EmptyState />
      ) : loading ? (
        <div className="flex justify-center items-center py-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">검색 중...</p>
          </div>
        </div>
      ) : results.length > 0 ? (
        <div className="bg-white flex flex-col gap-4">
          {results.map((result) => (
            <SearchResultCard key={result.id} {...result} />
          ))}
        </div>
      ) : (
        <EmptyState />
      )}

      {totalPages > 1 && (
        <PaginationControls
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={handlePageChange}
        />
      )}
    </div>
  );
}
