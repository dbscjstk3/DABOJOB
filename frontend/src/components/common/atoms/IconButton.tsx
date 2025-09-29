import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../../lib/utils';

const iconButtonVariants = cva(
  'inline-flex items-center justify-center rounded-full transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:cursor-not-allowed',
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
        sm: 'w-8 h-8',
        md: 'w-10 h-10',
        lg: 'w-12 h-12',
        xl: 'w-14 h-14 text-xl',
        '2xl': 'w-16 h-16 text-2xl',
        '3xl': 'w-20 h-20 text-3xl',
      },
      loading: { true: 'pointer-events-none opacity-70' },
    },
    defaultVariants: { variant: 'ghost', size: 'md' },
  },
);

type BaseProps = React.ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof iconButtonVariants> & {
    loading?: boolean;
  };

export function IconButton({
  className,
  variant,
  size,
  loading,
  ref, // ref를 prop으로
  type,
  children,
  ...rest
}: BaseProps & { ref?: React.Ref<HTMLButtonElement> }) {
  const classes = cn(iconButtonVariants({ variant, size, loading }), className);
  return (
    <button
      ref={ref}
      type={type ?? 'button'}
      className={classes}
      disabled={loading || rest.disabled}
      aria-busy={loading || undefined}
      {...rest}
    >
      {children}
    </button>
  );
}
