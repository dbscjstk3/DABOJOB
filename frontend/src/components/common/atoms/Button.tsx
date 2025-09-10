import React from 'react';
import classNames from 'classnames';

type ButtonVariant = 'contained' | 'outlined' | 'tag';
type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  startIcon?: React.ReactNode;
  endIcon?: React.ReactNode;
  selected?: boolean;
}

export function Button({
  className,
  variant = 'contained',
  size = 'md',
  startIcon,
  endIcon,
  selected,
  type,
  children,
  ...rest
}: ButtonProps) {
  const classes = classNames(
    'inline-flex items-center justify-center gap-2 rounded-lg text-sm transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
    {
      // size별 클래스
      'h-8 px-3 text-xs': size === 'sm',
      'h-10 px-4 text-sm': size === 'md',
      'h-12 px-6 text-base': size === 'lg',

      // variant별 클래스
      'px-7 h-10 bg-daboja-default text-white hover:bg-blue-700 disabled:bg-blue-300 focus-visible:ring-blue-500':
        variant === 'contained',
      'px-7 h-10 border border-daboja-default bg-transparent hover:bg-daboja-default hover:text-white disabled:opacity-60 text-daboja-default':
        variant === 'outlined',
      'px-3 py-1 bg-daboja-tag border border-slate-800 text-slate-800 hover:bg-daboja-default hover:text-white hover:border-transparent disabled:opacity-60 focus-visible:ring-slate-300':
        variant === 'tag' && !selected,
      'px-3 py-1 bg-daboja-default text-white border border-transparent disabled:opacity-60 focus-visible:ring-slate-300':
        variant === 'tag' && selected,
    },
    className, // 외부에서 추가 전달한 className 병합
  );

  return (
    <button type={type ?? 'button'} className={classes} {...rest}>
      {startIcon}
      <span className="whitespace-nowrap">{children}</span>
      {endIcon}
    </button>
  );
}
