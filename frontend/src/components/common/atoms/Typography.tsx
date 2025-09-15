import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../../lib/utils';

const typographyVariants = cva('font-pretendard', {
  variants: {
    variant: {
      //채용공고 전용
      recruits: 'text-[14px] leading-tight tracking-normal',
      //달력 네비게이션 전용
      calendarNavigation: 'text-[20px] md:text-[28px] leading-tight tracking-normal',
      //달력 숫자
      dayNumber: 'text-[18px] leading-tight tracking-normal',
      //기본 - 대부분 기본 크기
      default: 'text-[16px] leading-tight tracking-normal',
      //달력상세 보고서 제목, 직무명, 뉴스제목 등
      title: 'text-[24px] leading-tight tracking-normal',
    },
    weight: {
      thin: 'font-thin',
      extralight: 'font-extralight',
      light: 'font-light',
      regular: 'font-normal',
      medium: 'font-medium',
      semibold: 'font-semibold',
      bold: 'font-bold',
      extrabold: 'font-extrabold',
    },
    color: {
      black: 'text-black',
      dabojob: 'text-daboja-default',
      gray: 'text-[#757575]',
      red: 'text-[#FB2C36]',
      white: 'text-white',
    },
    align: {
      left: 'text-left',
      center: 'text-center',
      right: 'text-right',
      justify: 'text-justify',
    },
    lineHeight: {
      none: 'leading-none',
      tight: 'leading-tight',
      snug: 'leading-snug',
      normal: 'leading-normal',
      relaxed: 'leading-relaxed',
      loose: 'leading-loose',
    },
  },
  defaultVariants: {
    variant: 'default',
    weight: 'regular',
    color: 'black',
    align: 'left',
  },
});

export interface TypographyProps
  extends Omit<React.HTMLAttributes<HTMLElement>, 'color' | 'align'>,
    VariantProps<typeof typographyVariants> {
  /** 렌더링할 HTML 요소 */
  as?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6' | 'p' | 'span' | 'div';
  /** 추가 CSS 클래스 */
  className?: string;
  /** 자식 요소 */
  children: React.ReactNode;
}

/**
 * Typography 컴포넌트 - cva 기반
 */
export const Typography: React.FC<TypographyProps> = ({
  as = 'p',
  variant,
  weight,
  color,
  align,
  lineHeight,
  className,
  children,
  ...props
}) => {
  const Component = as as React.ElementType;

  return (
    <Component
      className={cn(typographyVariants({ variant, weight, color, align, lineHeight }), className)}
      {...props}
    >
      {children}
    </Component>
  );
};

export default Typography;
