import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../../lib/utils';

const typographyVariants = cva('font-pretendard', {
  variants: {
    variant: {
      h1: 'text-[57px] leading-[64px] tracking-[-0.25px]',
      h2: 'text-[45px] leading-[52px] tracking-normal',
      h3: 'text-[36px] leading-[44px] tracking-normal',
      h4: 'text-[32px] leading-[40px] tracking-normal',
      h5: 'text-[28px] leading-[36px] tracking-normal',
      h6: 'text-[24px] leading-[32px] tracking-normal',
      body: 'text-sm leading-5 tracking-[0.25px]',
      'body-lg': 'text-base leading-6 tracking-[0.5px]',
      'body-sm': 'text-xs leading-4 tracking-[0.4px]',
      label: 'text-sm leading-5 tracking-[0.1px]',
      'label-sm': 'text-[11px] leading-4 tracking-[0.5px]',
      caption: 'text-xs leading-4 tracking-[0.5px]',
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
      black: 'font-black',
    },
    color: {
      black: 'text-black',
      gray: 'text-gray-600',
      red: 'text-red-500',
      green: 'text-green-500',
      blue: 'text-blue-500',
      yellow: 'text-yellow-500',
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
    variant: 'body',
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
