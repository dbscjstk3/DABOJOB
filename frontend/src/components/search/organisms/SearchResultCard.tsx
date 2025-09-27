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
        'flex flex-col gap-2 md:gap-1 rounded-xl border border-slate-200 bg-white p-3 md:p-4 lg:p-6 hover:shadow-md transition-all cursor-pointer',
        className,
      )}
      onClick={handleCardClick}
    >
      {/* 모바일: 세로 배치 / 데스크톱: Grid 배치 */}
      <div className="flex flex-col md:grid md:grid-cols-[60px_150px_1fr_auto_auto] md:items-center gap-2 md:gap-4">
        {/* 상태 표시 */}
        <div
          className={cn(
            'py-0.5 md:px-3 md:py-1 rounded-md text-sm md:text-md font-medium flex-shrink-0',
            status === 'started' ? 'text-daboja-default' : 'text-red-500',
          )}
        >
          {status === 'started' ? '시작' : '마감'}
        </div>

        {/* 회사명 - 고정 너비 */}
        <Typography
          variant="default"
          weight="medium"
          className="text-gray-700 text-sm md:text-base truncate"
        >
          {companyName}
        </Typography>

        {/* 제목 */}
        <div className="flex-1 w-full md:w-auto">
          <ResultTitleLink
            title={title}
            className="text-sm md:text-base line-clamp-2 md:line-clamp-1"
          />
        </div>

        {/* 경력 */}
        <Typography variant="default" className="flex-shrink-0 text-xs md:text-base">
          {experienceLevel}
        </Typography>

        {/* 기간 */}
        <Typography variant="default" color="gray" className="flex-shrink-0 text-xs md:text-base">
          {period}
        </Typography>
      </div>

      {/* 하단: 직무 카테고리 */}
      <div className="md:grid md:grid-cols-[60px_150px_1fr_auto_auto] md:gap-4">
        <div className="hidden md:block"></div>
        <div className="hidden md:block"></div>
        <Typography variant="default" color="gray" className="text-xs md:text-sm">
          {jobCategory}
        </Typography>
        <div className="hidden md:block"></div>
        <div className="hidden md:block"></div>
      </div>
    </div>
  );
}
