import { Link } from '@tanstack/react-router';
import { ChevronsLeft, ChevronLeft, ArrowLeft } from 'lucide-react';
import { cn } from '@/lib/utils';

interface BackToCalendarLinkProps {
  to: string;
  label?: string;
  className?: string;
  iconType?: 'double' | 'single' | 'arrow';
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'muted' | 'primary';
}

export function BackToCalendarLink({
  to,
  label = '캘린더로 돌아가기',
  className = '',
  iconType = 'double',
  size = 'sm',
  variant = 'default',
}: BackToCalendarLinkProps) {
  const icons = {
    double: ChevronsLeft,
    single: ChevronLeft,
    arrow: ArrowLeft,
  };

  const sizes = {
    sm: {
      text: 'text-sm',
      icon: 'h-4 w-4',
      gap: 'gap-1.5',
    },
    md: {
      text: 'text-base',
      icon: 'h-5 w-5',
      gap: 'gap-2',
    },
    lg: {
      text: 'text-lg',
      icon: 'h-6 w-6',
      gap: 'gap-2.5',
    },
  };

  const variants = {
    default: 'text-slate-600 hover:text-slate-900',
    muted: 'text-gray-500 hover:text-gray-700',
    primary: 'bg-daboja-default hover:text-blue-700',
  };

  const Icon = icons[iconType];
  const sizeStyles = sizes[size];

  return (
    <Link
      to={to}
      className={cn(
        'inline-flex items-center font-medium transition-colors duration-200',
        sizeStyles.text,
        sizeStyles.gap,
        variants[variant],
        className,
      )}
      aria-label={label}
    >
      <Icon className={sizeStyles.icon} aria-hidden="true" />
      <span>{label}</span>
    </Link>
  );
}
