import React from 'react';
import classNames from 'classnames';

type IconButtonVariant = 'contained' | 'outlined' | 'ghost' | 'plain';
type IconButtonSize = 'sm' | 'md' | 'lg';

export interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: IconButtonVariant;
  size?: IconButtonSize;
}

export function IconButton({
  className,
  variant = 'ghost',
  size = 'md',
  children,
  ...rest
}: IconButtonProps) {
  const classes = classNames(
    'inline-flex items-center justify-center rounded-full transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
    {
      // size
      'w-8 h-8 text-sm': size === 'sm', // 32px
      'w-10 h-10 text-base': size === 'md', // 40px
      'w-12 h-12 text-lg': size === 'lg', // 48px

      // variant
      'bg-daboja-default text-white hover:bg-blue-700 disabled:bg-blue-300 focus-visible:ring-blue-500':
        variant === 'contained',
      'border border-slate-300 text-slate-800 hover:bg-slate-50 disabled:opacity-60':
        variant === 'outlined',
      'text-slate-800 hover:bg-slate-100 disabled:opacity-60': variant === 'ghost',
      'text-slate-600 hover:text-slate-900 disabled:opacity-60': variant === 'plain',
    },
    className,
  );

  return (
    <button type="button" className={classes} {...rest}>
      {children}
    </button>
  );
}
