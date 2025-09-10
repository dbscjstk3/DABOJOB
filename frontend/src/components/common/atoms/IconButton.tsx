import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../../lib/utils';

const iconButtonVariants = cva(
  'inline-flex items-center justify-center rounded-full transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
  {
    variants: {
      variant: {
        contained:
          'bg-daboja-default text-white hover:bg-blue-700 disabled:bg-blue-300 focus-visible:ring-blue-500',
        outlined: 'border border-slate-300 text-slate-800 hover:bg-slate-50 disabled:opacity-60',
        ghost: 'text-slate-800 hover:bg-slate-100 disabled:opacity-60',
        plain: 'text-slate-600 hover:text-slate-900 disabled:opacity-60',
      },
      size: {
        sm: 'w-8 h-8 text-sm',
        md: 'w-10 h-10 text-base',
        lg: 'w-12 h-12 text-lg',
      },
    },
    defaultVariants: {
      variant: 'ghost',
      size: 'md',
    },
  },
);

export interface IconButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof iconButtonVariants> {}

export function IconButton({ className, variant, size, children, ...rest }: IconButtonProps) {
  const classes = cn(iconButtonVariants({ variant, size }), className);

  return (
    <button type="button" className={classes} {...rest}>
      {children}
    </button>
  );
}
