import { useState, useRef, useEffect } from 'react';
import { useNavigate } from '@tanstack/react-router';
import { cn } from '@/lib/utils';
import Typography from '@/components/common/atoms/Typography';
import type { AutocompleteJobPosting } from '@/lib/api';

interface AutocompleteDropdownProps {
  items: AutocompleteJobPosting[];
  isOpen: boolean;
  onClose: () => void;
  onItemClick?: (item: AutocompleteJobPosting) => void;
  className?: string;
}

export default function AutocompleteDropdown({
  items,
  isOpen,
  onClose,
  onItemClick,
  className,
}: AutocompleteDropdownProps) {
  const navigate = useNavigate();
  const dropdownRef = useRef<HTMLDivElement>(null);
  const [selectedIndex, setSelectedIndex] = useState(-1);

  // 외부 클릭 감지
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose]);

  // 키보드 네비게이션
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen || items.length === 0) return;

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex((prev) => (prev < items.length - 1 ? prev + 1 : 0));
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex((prev) => (prev > 0 ? prev - 1 : items.length - 1));
          break;
        case 'Enter':
          e.preventDefault();
          if (selectedIndex >= 0 && selectedIndex < items.length) {
            handleItemClick(items[selectedIndex]);
          }
          break;
        case 'Escape':
          e.preventDefault();
          onClose();
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, items, selectedIndex, onClose]);

  const handleItemClick = (item: AutocompleteJobPosting) => {
    if (onItemClick) {
      onItemClick(item);
    } else {
      // 기본 동작: 캘린더 상세 페이지로 이동
      // companyId를 summaryId로 사용
      // 실제로는 API 수정이 필요할 수 있음
      navigate({
        to: '/calendar/$id',
        params: { id: String(item.companyId) },
        search: { jobPostingId: String(item.jobPostingId) },
      });
    }
    onClose();
  };

  const formatDeadline = (dateString: string): string => {
    const date = new Date(dateString);
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `~${month}.${day}`;
  };

  const getJobStatus = (deadlineDate: string): 'started' | 'ended' => {
    const today = new Date();
    const deadline = new Date(deadlineDate);
    return deadline >= today ? 'started' : 'ended';
  };

  if (!isOpen || items.length === 0) return null;

  return (
    <div className="relative">
      {/* 드롭다운 리스트 */}
      <div
        ref={dropdownRef}
        className={cn(
          'absolute top-full left-0 mt-1 w-full bg-white border border-slate-200 rounded-lg shadow-lg overflow-hidden z-50',
          className,
        )}
      >
        <div className="max-h-[400px] overflow-y-auto">
          {items.map((item, index) => (
            <div
              key={item.jobPostingId}
              className={cn(
                'px-4 py-3 hover:bg-slate-50 cursor-pointer transition-colors border-b border-slate-100 last:border-b-0',
                selectedIndex === index && 'bg-slate-50',
              )}
              onClick={() => handleItemClick(item)}
              onMouseEnter={() => {
                setSelectedIndex(index);
              }}
            >
              <div className="flex items-center gap-3">
                {/* 상태 */}
                <Typography
                  variant="default"
                  weight="medium"
                  className={cn(
                    'text-sm',
                    getJobStatus(item.deadlineDate) === 'started'
                      ? 'text-daboja-default'
                      : 'text-red-500',
                  )}
                >
                  {getJobStatus(item.deadlineDate) === 'started' ? '시작' : '마감'}
                </Typography>

                {/* 회사명 - 직무명 */}
                <Typography variant="default" weight="medium" className="flex-1">
                  {item.companyName} - {item.title}
                </Typography>

                {/* 마감일 */}
                <Typography variant="default" color="gray" className="text-sm">
                  {formatDeadline(item.deadlineDate)}
                </Typography>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 호버 카드 (미리보기) */}
      {/* {hoveredItem && (
        <div className="absolute left-[calc(100%+12px)] top-0 w-[400px] z-50 pointer-events-none">
          <SearchResultCard
            status={getJobStatus(hoveredItem.deadlineDate)}
            companyName={hoveredItem.companyName}
            title={hoveredItem.title}
            experienceLevel={hoveredItem.careerInfo}
            period={formatDeadline(hoveredItem.deadlineDate)}
            jobCategory={`${hoveredItem.jobSectorCategory} · ${hoveredItem.jobSectorName}`}
            url={hoveredItem.url}
            className="shadow-xl"
          />
        </div>
      )} */}
    </div>
  );
}
