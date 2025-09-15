import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../../lib/utils';
import { Typography } from '../../common/atoms/Typography';

const badgeVariants = cva('inline-flex items-center gap-1', {
  variants: {
    type: {
      start: '',
      end: '',
    },
  },
  defaultVariants: {
    type: 'start',
  },
});

export interface RecruitBadgeProps
  extends Omit<React.HTMLAttributes<HTMLDivElement>, 'color'>,
    VariantProps<typeof badgeVariants> {
  company: string;
}

export const RecruitBadge: React.FC<RecruitBadgeProps> = ({
  type,
  company,
  className,
  ...props
}) => {
  return (
    <div className={cn(badgeVariants({ type }), className)} {...props}>
      <Typography variant="recruits" weight="bold" color={type === 'start' ? 'dabojob' : 'red'}>
        {type === 'start' ? '시작' : '종료'}
      </Typography>
      {company && (
        <Typography
          variant="recruits"
          className={cn('truncate max-w-[8rem]')}
          weight="regular"
          color="black"
        >
          {company}
        </Typography>
      )}
    </div>
  );
};

export default RecruitBadge;
