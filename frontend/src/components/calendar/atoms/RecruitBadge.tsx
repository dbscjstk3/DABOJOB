import React from 'react';
import { useNavigate } from '@tanstack/react-router';
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
  companyId?: number;
  jobPostingId?: number;
}

export const RecruitBadge: React.FC<RecruitBadgeProps> = ({
  type,
  company,
  companyId,
  jobPostingId,
  className,
  ...props
}) => {
  const navigate = useNavigate();

  // 기업 상세페이지로 이동하는 함수
  const handleClick = () => {
    if (companyId && jobPostingId) {
      navigate({
        to: '/calendar/$id',
        params: { id: companyId.toString() },
        search: { jobPostingId: jobPostingId.toString() },
      });
    }
  };

  return (
    <div
      className={cn(
        badgeVariants({ type }),
        companyId && jobPostingId
          ? 'cursor-pointer hover:bg-gray-100 hover:shadow-sm hover:scale-105 transition-all duration-200 ease-in-out rounded-md px-1 py-0.5'
          : '',
        className,
      )}
      onClick={handleClick}
      {...props}
    >
      <Typography
        variant="recruits"
        weight="bold"
        color={type === 'start' ? 'dabojob' : 'red'}
        className={cn(companyId && jobPostingId ? 'transition-colors duration-200' : '')}
      >
        {type === 'start' ? '시작' : '종료'}
      </Typography>
      {company && (
        <Typography
          variant="recruits"
          className={cn(
            'truncate max-w-[8rem]',
            companyId && jobPostingId ? 'transition-colors duration-200 hover:text-blue-600' : '',
          )}
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
