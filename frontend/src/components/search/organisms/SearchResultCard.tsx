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
      {/* 모바일: 세로 배치 / 데스크톱: 가로 배치 */}
      <div className="flex flex-col md:flex-row md:items-center gap-2 md:gap-4">
        {/* 상단 정보 (모바일: 가로 / 데스크톱: 그대로) */}
        <div className="flex items-center gap-2 md:gap-4 flex-wrap md:flex-nowrap">
          {/* 상태 표시 */}
          <div
            className={cn(
              'py-0.5 md:px-3 md:py-1 rounded-md text-sm md:text-md font-medium flex-shrink-0',
              status === 'started' ? 'text-daboja-default' : 'text-red-500',
            )}
          >
            {status === 'started' ? '시작' : '마감'}
          </div>

          {/* 회사명 */}
          <Typography
            variant="default"
            weight="medium"
            className="text-gray-700 flex-shrink-0 text-sm md:text-base md:mr-3"
          >
            {companyName}
          </Typography>

          {/* 모바일: 경력, 기간 */}
          <div className="flex items-center gap-2 md:hidden ml-auto">
            <Typography variant="default" className="text-xs">
              {experienceLevel}
            </Typography>
            <Typography variant="default" color="gray" className="text-xs">
              {period}
            </Typography>
          </div>
        </div>

        {/* 제목 - 모바일에서 전체 너비 사용 */}
        <div className="flex-1 w-full md:w-auto">
          <ResultTitleLink
            title={title}
            className="text-sm md:text-base line-clamp-2 md:line-clamp-1"
          />
        </div>

        {/* 데스크톱: 신입/경력, 기간 */}
        <div className="hidden md:flex items-center gap-4">
          <Typography variant="default" className="flex-shrink-0">
            {experienceLevel}
          </Typography>
          <Typography variant="default" color="gray" className="flex-shrink-0">
            {period}
          </Typography>
        </div>
      </div>

      {/* 하단: 직무 카테고리 */}
      <div className="md:pl-[150px]">
        <Typography variant="default" color="gray" className="text-xs md:text-sm">
          {jobCategory}
        </Typography>
      </div>
    </div>
  );
}
