import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../../lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 rounded-lg text-sm transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
  {
    variants: {
      variant: {
        contained:
          'bg-daboja-default text-white hover:bg-blue-700 disabled:bg-blue-300 focus-visible:ring-blue-500',
        outlined:
          'border border-daboja-default bg-transparent hover:bg-daboja-default hover:text-white disabled:opacity-60 text-daboja-default',
        tag: 'px-3 py-1 border text-slate-800 disabled:opacity-60 focus-visible:ring-slate-300',
      },
      size: {
        sm: 'h-8 px-3 text-xs',
        md: 'h-10 px-4 text-sm',
        lg: 'h-12 px-6 text-base',
      },
    },
    defaultVariants: {
      variant: 'contained',
      size: 'md',
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  startIcon?: React.ReactNode;
  endIcon?: React.ReactNode;
  selected?: boolean;
}

export function Button({
  className,
  variant,
  size,
  startIcon,
  endIcon,
  selected,
  type,
  children,
  ...rest
}: ButtonProps) {
  const classes = cn(
    buttonVariants({ variant, size }),
    {
      // variant가 contained나 outlined일 때는 px-7 h-10 적용
      'px-7 h-10': variant === 'contained' || variant === 'outlined',
      // tag variant의 selected 상태 처리
      'bg-daboja-tag border-slate-800 hover:bg-daboja-default hover:text-white hover:border-transparent':
        variant === 'tag' && !selected,
      'bg-daboja-default text-white border-transparent': variant === 'tag' && selected,
    },
    className,
  );

  return (
    <button type={type ?? 'button'} className={classes} {...rest}>
      {startIcon}
      <span className="whitespace-nowrap">{children}</span>
      {endIcon}
    </button>
  );
}
