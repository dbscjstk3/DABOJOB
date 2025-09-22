import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../../lib/utils';
import { RecruitBadge } from './RecruitBadge';
import { Typography } from '../../common/atoms/Typography';
import type { JobPostingResponse } from '@/lib/api';

const cellBoxVariants = cva('flex flex-col border-t border-daboja-default p-2 h-20 md:h-72', {
  variants: {
    tone: {
      default: 'bg-white',
      muted: 'bg-slate-100 text-slate-500',
    },
    today: {
      false: '',
      true: 'bg-slate-50',
    },
    interactive: {
      false: '',
      true: 'cursor-pointer hover:bg-slate-100 hover:shadow-sm',
    },
  },
  defaultVariants: {
    tone: 'default',
    today: false,
    interactive: true,
  },
});

export interface CellBoxProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cellBoxVariants> {
  /** 추가 CSS 클래스 */
  className?: string;
  /** 자식 요소 */
  children?: React.ReactNode;
  /** 날짜 */
  day?: number | null;
  /** 요일 (0: 일요일, 1: 월요일, ..., 6: 토요일) */
  dayOfWeek?: number;
  /** 공고 데이터 */
  recruits?: JobPostingResponse[];
  /** 확장 상태 */
  isExpanded?: boolean;
  /** 확장 토글 함수 */
  onToggleExpanded?: (day: number) => void;
  /** 모달 열기 함수 */
  onOpenModal?: (day: number) => void;
}

/**
 * CellBox 컴포넌트 - cva 기반
 */
export const CellBox: React.FC<CellBoxProps> = ({
  tone,
  today,
  interactive,
  className,
  children,
  day,
  dayOfWeek,
  recruits = [],
  isExpanded = false,
  onToggleExpanded: _onToggleExpanded,
  onOpenModal,
  ...props
}) => {
  return (
    <div
      tabIndex={0}
      role="gridcell"
      className={cn(cellBoxVariants({ tone, today, interactive }), className)}
      onClick={() => {
        if (day && recruits.length > 0) {
          onOpenModal?.(day);
        }
      }}
      style={{ cursor: day && recruits.length > 0 ? 'pointer' : 'default' }}
      {...props}
    >
      {day && (
        <div className="flex flex-col h-full mt-2 gap-2">
          <div className="flex items-center justify-start">
            {today ? (
              <div className="w-7 h-7 bg-[#099AEE] rounded-full flex items-center justify-center">
                <Typography variant="dayNumber" color="white" weight="bold" align="center">
                  {day}
                </Typography>
              </div>
            ) : (
              <div className="w-7 h-7 rounded-full flex items-center justify-center">
                <Typography
                  variant="dayNumber"
                  color={
                    tone === 'default'
                      ? dayOfWeek === 0
                        ? 'red'
                        : dayOfWeek === 6
                          ? 'dabojob'
                          : 'black'
                      : 'gray'
                  }
                  weight="regular"
                  align="center"
                >
                  {day}
                </Typography>
              </div>
            )}
          </div>
          {/* 공고 배지 렌더링 */}
          <div className="flex flex-col gap-1">
            {recruits.length > 0 && (
              <>
                {/* 모바일: 개수만 표시, 데스크톱: 개별 공고 표시 */}
                <div className="block md:hidden">
                  <div className="flex items-center justify-center">
                    <div className="bg-blue-100 text-black text-xs px-2 py-1 rounded-full font-medium">
                      +{recruits.length}
                    </div>
                  </div>
                </div>

                {/* 데스크톱: 개별 공고 표시 */}
                <div className="hidden md:flex md:flex-col md:gap-1">
                  {(isExpanded ? recruits : recruits.slice(0, 8)).map((item, idx) => {
                    // 공고가 해당 날짜에 공고일인지 마감일인지 구분
                    const postingDate = new Date(item.postingDate);
                    const isPostingDate = postingDate.getDate() === day;

                    return (
                      <RecruitBadge
                        key={idx}
                        type={isPostingDate ? 'start' : 'end'}
                        company={item.companyName}
                      />
                    );
                  })}
                  {recruits.length > 8 && (
                    <button
                      type="button"
                      className="text-left"
                      onClick={(e) => {
                        e.stopPropagation();
                        onOpenModal?.(day);
                      }}
                    >
                      <Typography variant="recruits" color="gray">
                        +{recruits.length - 8} 더보기
                      </Typography>
                    </button>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      )}
      {children}
    </div>
  );
};

export default CellBox;
