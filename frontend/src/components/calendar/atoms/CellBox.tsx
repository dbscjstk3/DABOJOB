import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../../lib/utils';
import { RecruitBadge } from './RecruitBadge';
import { Typography } from '../../common/atoms/Typography';

const cellBoxVariants = cva('flex flex-col border-t border-daboja-default p-2 h-72', {
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
  /** 공고 데이터 */
  recruits?: {
    type: 'start' | 'end';
    company: string;
    employmentType: string;
    jobCategory: string;
  }[];
  /** 확장 상태 */
  isExpanded?: boolean;
  /** 확장 토글 함수 */
  onToggleExpanded?: (day: number) => void;
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
  recruits = [],
  isExpanded = false,
  onToggleExpanded,
  ...props
}) => {
  return (
    <div
      tabIndex={0}
      role="gridcell"
      className={cn(cellBoxVariants({ tone, today, interactive }), className)}
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
              <Typography
                variant="dayNumber"
                color={tone === 'default' ? 'black' : 'gray'}
                weight="regular"
                align="left"
              >
                {day}
              </Typography>
            )}
          </div>
          {/* 공고 배지 렌더링 */}
          <div className="flex flex-col gap-1">
            {recruits.length > 0 && (
              <>
                {(isExpanded ? recruits : recruits.slice(0, 8)).map((item, idx) => (
                  <RecruitBadge key={idx} type={item.type} company={item.company} />
                ))}
                {recruits.length > 8 && (
                  <button
                    type="button"
                    className="text-left"
                    onClick={() => onToggleExpanded?.(day)}
                  >
                    <Typography variant="recruits" color="gray">
                      {isExpanded ? '접기' : `+${recruits.length - 8} 더보기`}
                    </Typography>
                  </button>
                )}
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
