import Typography from '@/components/common/atoms/Typography';
import ResultTitleLink from '@/components/search/molecules/ResultTitleLink';
import { useNavigate } from '@tanstack/react-router';
import { cn } from '@/lib/utils';

interface SearchResultCardProps {
  status: 'started' | 'ended';
  companyName: string;
  title: string;
  experienceLevel: string;
  period: string;
  jobCategory: string;
  url?: string;
  className?: string;
  companyId: number;
  jobPostingId: number;
}

export default function SearchResultCard({
  status,
  companyName,
  title,
  experienceLevel,
  period,
  jobCategory,
  className = '',
  companyId,
  jobPostingId,
}: SearchResultCardProps) {
  const navigate = useNavigate();

  const handleCardClick = () => {
    // 달력 상세 페이지로 이동 (companyId를 summaryId로 사용)
    navigate({
      to: '/calendar/$id',
      params: { id: String(companyId) },
      search: { jobPostingId: String(jobPostingId) },
    });
  };

  return (
    <div
      className={cn(
        'flex flex-col gap-2 md:gap-1 rounded-xl border border-slate-200 bg-white p-3 sm:p-4 md:p-5 lg:p-6 hover:shadow-md transition-all cursor-pointer',
        className,
      )}
      onClick={handleCardClick}
    >
      {/* 모바일: 2줄 구조 / 데스크톱: Grid 배치 */}
      <div className="flex flex-col gap-2 md:grid md:grid-cols-[60px_200px_1fr_auto_auto] lg:grid-cols-[60px_150px_1fr_auto_auto] md:items-center md:gap-4">
        {/* 모바일 상단: 상태 + 회사명 | 경력 + 기간 */}
        <div className="flex items-center justify-between md:hidden">
          <div className="flex items-center gap-2">
            {/* 상태 표시 (모바일) */}
            <div
              className={cn(
                'py-0.5 text-xs font-medium flex-shrink-0',
                status === 'started' ? 'text-daboja-default' : 'text-red-500',
              )}
            >
              {status === 'started' ? '시작' : '마감'}
            </div>

            {/* 회사명 (모바일) */}
            <Typography
              variant="default"
              weight="medium"
              className="text-gray-700 text-sm truncate"
            >
              {companyName}
            </Typography>
          </div>

          {/* 모바일 우측: 경력 + 기간 */}
          <div className="flex items-center gap-2">
            <Typography variant="default" className="flex-shrink-0 text-xs sm:text-sm">
              {experienceLevel}
            </Typography>
            <Typography variant="default" color="gray" className="flex-shrink-0 text-xs sm:text-sm">
              {period}
            </Typography>
          </div>
        </div>

        {/* 데스크톱: 상태 */}
        <div
          className={cn(
            'hidden md:block px-3 py-1 text-sm font-medium',
            status === 'started' ? 'text-daboja-default' : 'text-red-500',
          )}
        >
          {status === 'started' ? '시작' : '마감'}
        </div>

        {/* 데스크톱: 회사명 */}
        <Typography
          variant="default"
          weight="medium"
          className="hidden md:block text-gray-700 text-base truncate"
        >
          {companyName}
        </Typography>

        {/* 제목 */}
        <div>
          <ResultTitleLink
            title={title}
            className="text-sm sm:text-base line-clamp-2 md:line-clamp-1"
          />
        </div>

        {/* 데스크톱: 경력 */}
        <Typography variant="default" className="hidden md:block flex-shrink-0 text-base">
          {experienceLevel}
        </Typography>

        {/* 데스크톱: 기간 */}
        <Typography
          variant="default"
          color="gray"
          className="hidden md:block flex-shrink-0 text-base"
        >
          {period}
        </Typography>
      </div>

      {/* 하단: 직무 카테고리 */}
      <div className="md:grid md:grid-cols-[60px_200px_1fr_auto_auto] lg:grid-cols-[60px_150px_1fr_auto_auto] md:gap-4">
        <div className="hidden md:block"></div>
        <div className="hidden md:block"></div>
        <Typography variant="default" color="gray" className="text-xs sm:text-sm">
          {jobCategory}
        </Typography>
        <div className="hidden md:block"></div>
        <div className="hidden md:block"></div>
      </div>
    </div>
  );
}
