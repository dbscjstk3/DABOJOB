import { ChevronLeft, ChevronRight } from 'lucide-react';
import Typography from '@/components/common/atoms/Typography';
import { cn } from '@/lib/utils';

interface PaginationControlsProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  onPageHover?: (page: number) => void;
  className?: string;
}

export default function PaginationControls({
  currentPage,
  totalPages,
  onPageChange,
  onPageHover,
  className = '',
}: PaginationControlsProps) {
  if (totalPages <= 1) return null;

  const generatePageNumbers = () => {
    const pages: number[] = [];
    // 모바일: 3개, 태블릿/데스크톱: 5개
    const pageGroupSize = window.innerWidth < 640 ? 3 : 5;

    // 현재 페이지가 속한 그룹 계산
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
    <div className={cn('flex justify-center items-center gap-1 sm:gap-2 mt-6 md:mt-8', className)}>
      {/* 이전 버튼 */}
      <button
        onClick={() => onPageChange(currentPage - 1)}
        onMouseEnter={() => currentPage > 1 && onPageHover?.(currentPage - 1)}
        disabled={currentPage === 1}
        className={cn(
          'flex items-center gap-0.5 sm:gap-1 px-2 sm:px-3 py-1.5 sm:py-2 rounded-md text-xs sm:text-sm transition-colors',
          currentPage === 1
            ? 'text-gray-400 cursor-not-allowed'
            : 'text-gray-700 hover:bg-gray-100',
        )}
      >
        <ChevronLeft className="h-3 w-3 sm:h-4 sm:w-4" />
        <span className="hidden sm:inline">이전</span>
      </button>

      {/* 페이지 번호들 */}
      <div className="flex items-center gap-0.5 sm:gap-1">
        {pageNumbers.map((page, index) => (
          <button
            key={index}
            onClick={() => onPageChange(page)}
            onMouseEnter={() => onPageHover?.(page)}
            className={cn(
              'w-8 h-8 sm:w-10 sm:h-10 flex items-center justify-center rounded-md text-xs sm:text-sm transition-colors',
              page === currentPage ? 'bg-blue-600 text-white' : 'text-gray-700 hover:bg-gray-100',
            )}
          >
            <Typography variant="default" className="text-inherit text-xs sm:text-sm">
              {page}
            </Typography>
          </button>
        ))}
      </div>

      {/* 다음 버튼 */}
      <button
        onClick={() => onPageChange(currentPage + 1)}
        onMouseEnter={() => currentPage < totalPages && onPageHover?.(currentPage + 1)}
        disabled={currentPage === totalPages}
        className={cn(
          'flex items-center gap-0.5 sm:gap-1 px-2 sm:px-3 py-1.5 sm:py-2 rounded-md text-xs sm:text-sm transition-colors',
          currentPage === totalPages
            ? 'text-gray-400 cursor-not-allowed'
            : 'text-gray-700 hover:bg-gray-100',
        )}
      >
        <span className="hidden sm:inline">다음</span>
        <ChevronRight className="h-3 w-3 sm:h-4 sm:w-4" />
      </button>
    </div>
  );
}
