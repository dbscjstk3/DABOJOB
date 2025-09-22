import { useSearch, useNavigate } from '@tanstack/react-router';
import { useSearchJobPostings } from '@/lib/hooks';
import SearchResultCard from '@/components/search/organisms/SearchResultCard';
import PaginationControls from '@/components/search/molecules/PaginationControls';
import EmptyState from '@/components/search/molecules/EmptyState';
import Typography from '@/components/common/atoms/Typography';

// 검색 파라미터 타입 정의
interface SearchParams {
  q?: string;
  page?: number;
}

export default function SearchDetailPage() {
  const navigate = useNavigate({ from: '/search' });
  const searchParams = useSearch({ from: '/search' }) as SearchParams;
  const query = searchParams.q || '';
  const currentPage = (searchParams.page || 1) - 1; // API는 0부터 시작

  // React Query를 사용한 데이터 fetching
  const { data, isLoading, isError } = useSearchJobPostings(query, currentPage, 20);

  // 날짜 포맷 함수
  const formatPeriod = (deadline: string): string => {
    const date = new Date(deadline);
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `~${month}/${day}`;
  };

  // 상태 계산 함수
  const getStatus = (deadline: string): 'started' | 'ended' => {
    const today = new Date();
    const deadlineDate = new Date(deadline);
    return deadlineDate >= today ? 'started' : 'ended';
  };

  // 경력 정보 변환 함수
  const formatCareerInfo = (careerInfo: string): string => {
    const careerMap: { [key: string]: string } = {
      NEWBIE: '신입',
      JUNIOR: '주니어',
      SENIOR: '시니어',
    };
    return careerMap[careerInfo] || careerInfo;
  };

  // 페이지 변경 핸들러
  const handlePageChange = (newPage: number) => {
    navigate({
      search: (prev) => ({
        ...prev,
        page: newPage, // UI는 1부터 시작
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
      ) : isLoading ? (
        <div className="flex justify-center items-center py-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">검색 중...</p>
          </div>
        </div>
      ) : isError ? (
        <div className="flex justify-center items-center py-12">
          <div className="text-center text-red-600">
            <p>검색 중 오류가 발생했습니다. 다시 시도해주세요.</p>
          </div>
        </div>
      ) : data && data.content.length > 0 ? (
        <div className="bg-white flex flex-col gap-4">
          {data.content.map((job) => (
            <SearchResultCard
              key={job.jobPostingId}
              status={getStatus(job.deadlineDate)}
              companyName={job.companyName}
              title={job.title}
              experienceLevel={formatCareerInfo(job.careerInfo)}
              period={formatPeriod(job.deadlineDate)}
              jobCategory={`${job.jobSectorCategory} · ${job.jobSectorName}`}
              url={job.url}
              companyId={job.companyId}
              jobPostingId={job.jobPostingId}
            />
          ))}
        </div>
      ) : (
        <EmptyState />
      )}

      {data && data.totalPages > 1 && (
        <PaginationControls
          currentPage={currentPage + 1} // UI는 1부터 표시
          totalPages={data.totalPages}
          onPageChange={handlePageChange}
        />
      )}
    </div>
  );
}
