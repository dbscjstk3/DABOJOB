import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../../lib/utils';

const cellBoxVariants = cva('flex flex-col border-t border-[#099AEE] p-2 h-72', {
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
  children: React.ReactNode;
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
  ...props
}) => {
  return (
    <div
      tabIndex={0}
      role="gridcell"
      className={cn(cellBoxVariants({ tone, today, interactive }), className)}
      {...props}
    >
      {children}
    </div>
  );
};

export default CellBox;
