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
  url,
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

  const handleTitleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (url) {
      window.open(url, '_blank');
    }
  };

  return (
    <div
      className={cn(
        'flex flex-col gap-1 rounded-xl border border-slate-200 bg-white p-4 md:p-6  hover:shadow-md transition-all cursor-pointer',
        className,
      )}
      onClick={handleCardClick}
    >
      {/* 상단: 모든 요소를 한 줄에 정렬 */}
      <div className="flex items-center gap-4">
        {/* 상태 표시 */}
        <div
          className={cn(
            'px-3 py-1 rounded-md text-md font-medium flex-shrink-0',
            status === 'started' ? 'text-daboja-default' : 'text-red-500',
          )}
        >
          {status === 'started' ? '시작' : '마감'}
        </div>

        {/* 회사명 */}
        <Typography variant="default" weight="medium" className="text-gray-700 flex-shrink-0 mr-3">
          {companyName}
        </Typography>

        {/* 제목 */}
        <div className="flex-1" onClick={handleTitleClick}>
          <ResultTitleLink title={title} url={url} className="text-base" />
        </div>

        {/* 신입/경력 */}
        <Typography variant="default" className="flex-shrink-0">
          {experienceLevel}
        </Typography>

        {/* 기간 */}
        <Typography variant="default" color="gray" className="flex-shrink-0">
          {period}
        </Typography>
      </div>

      {/* 하단: 직무 카테고리 */}
      <div className="pl-[150px]">
        <Typography variant="default" color="gray" className="text-sm">
          {jobCategory}
        </Typography>
      </div>
    </div>
  );
}
