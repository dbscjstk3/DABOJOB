import { ChevronLeft, ChevronRight } from 'lucide-react';
import Typography from '@/components/common/atoms/Typography';
import { cn } from '@/lib/utils';

interface PaginationControlsProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  className?: string;
}

export default function PaginationControls({
  currentPage,
  totalPages,
  onPageChange,
  className = '',
}: PaginationControlsProps) {
  if (totalPages <= 1) return null;

  const generatePageNumbers = () => {
    const pages: number[] = [];
    const pageGroupSize = 5;

    // 현재 페이지가 속한 그룹 계산 (1-5는 그룹 1, 6-10은 그룹 2...)
    const currentGroup = Math.ceil(currentPage / pageGroupSize);
    const startPage = (currentGroup - 1) * pageGroupSize + 1;
    const endPage = Math.min(startPage + pageGroupSize - 1, totalPages);

    // 해당 그룹의 페이지들만 표시
    for (let i = startPage; i <= endPage; i++) {
      pages.push(i);
    }

    return pages;
  };

  const pageNumbers = generatePageNumbers();

  return (
    <div className={cn('flex justify-center items-center gap-2 mt-8', className)}>
      {/* 이전 버튼 */}
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className={cn(
          'flex items-center gap-1 px-3 py-2 rounded-md text-sm transition-colors',
          currentPage === 1
            ? 'text-gray-400 cursor-not-allowed'
            : 'text-gray-700 hover:bg-gray-100',
        )}
      >
        <ChevronLeft className="h-4 w-4" />
        <span>이전</span>
      </button>

      {/* 페이지 번호들 */}
      <div className="flex items-center gap-1">
        {pageNumbers.map((page, index) => (
          <button
            key={index}
            onClick={() => onPageChange(page)}
            className={cn(
              'w-10 h-10 flex items-center justify-center rounded-md text-sm transition-colors',
              page === currentPage ? 'bg-blue-600 text-white' : 'text-gray-700 hover:bg-gray-100',
            )}
          >
            <Typography variant="default" className="text-inherit">
              {page}
            </Typography>
          </button>
        ))}
      </div>

      {/* 다음 버튼 */}
      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className={cn(
          'flex items-center gap-1 px-3 py-2 rounded-md text-sm transition-colors',
          currentPage === totalPages
            ? 'text-gray-400 cursor-not-allowed'
            : 'text-gray-700 hover:bg-gray-100',
        )}
      >
        <span>다음</span>
        <ChevronRight className="h-4 w-4" />
      </button>
    </div>
  );
}
