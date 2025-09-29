import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../../lib/utils';

const dayVariants = cva('p-2 text-center font-bold', {
  variants: {
    dayOfWeek: {
      sunday: 'text-red-500',
      monday: 'text-gray-600',
      tuesday: 'text-gray-600',
      wednesday: 'text-gray-600',
      thursday: 'text-gray-600',
      friday: 'text-gray-600',
      saturday: 'text-daboja-default',
    },
  },
  defaultVariants: {
    dayOfWeek: 'monday',
  },
});

export interface DayProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof dayVariants> {
  /** 요일 텍스트 */
  children: React.ReactNode;
  /** 추가 CSS 클래스 */
  className?: string;
}

/**
 * Day 컴포넌트 - 요일 표시용 atom
 * 일요일: 빨간색, 토요일: 파란색, 나머지: 회색
 */
export const Day: React.FC<DayProps> = ({ dayOfWeek, className, children, ...props }) => {
  return (
    <div className={cn(dayVariants({ dayOfWeek }), className)} {...props}>
      {children}
    </div>
  );
};

export default Day;
