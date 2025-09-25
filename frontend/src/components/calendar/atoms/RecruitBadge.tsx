import React from 'react';
import { useNavigate } from '@tanstack/react-router';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../../lib/utils';
import { Typography } from '../../common/atoms/Typography';
import type { AdminCalendarCompany } from '@/lib/api';

const badgeVariants = cva('inline-flex items-center gap-1', {
  variants: {
    type: {
      start: '',
      end: '',
      pending: '',
      processing: '',
      suggested: '',
      verified: '',
      rejected: '',
      failed: '',
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
  // 관리자용 props
  adminCompany?: AdminCalendarCompany;
  onAdminCalendarCompanyClick?: (company: AdminCalendarCompany) => void;
}

export const RecruitBadge: React.FC<RecruitBadgeProps> = ({
  type,
  company,
  companyId,
  jobPostingId,
  adminCompany,
  onAdminCalendarCompanyClick,
  className,
  ...props
}) => {
  const navigate = useNavigate();

  // 기업 상세페이지로 이동하는 함수
  const handleClick = () => {
    // 관리자용 클릭 핸들러
    if (adminCompany && onAdminCalendarCompanyClick) {
      onAdminCalendarCompanyClick(adminCompany);
      return;
    }

    // 일반 사용자용 클릭 핸들러
    if (companyId && jobPostingId) {
      navigate({
        to: '/calendar/$id',
        params: { id: companyId.toString() },
        search: { jobPostingId: jobPostingId.toString() },
      });
    }
  };

  // 관리자용 텍스트와 색상 결정
  const getStatusText = () => {
    switch (type) {
      case 'pending':
        return '대기';
      case 'processing':
        return '처리중';
      case 'suggested':
        return '제안됨';
      case 'verified':
        return '확인됨';
      case 'rejected':
        return '거부됨';
      case 'failed':
        return '실패';
      case 'start':
        return '시작';
      case 'end':
        return '종료';
      default:
        return '';
    }
  };

  const getStatusColor = () => {
    switch (type) {
      case 'pending':
        return 'gray';
      case 'processing':
        return 'dabojob';
      case 'suggested':
        return 'yellow';
      case 'verified':
        return 'green';
      case 'rejected':
        return 'red';
      case 'failed':
        return 'red';
      case 'start':
        return 'dabojob';
      case 'end':
        return 'red';
      default:
        return 'black';
    }
  };

  const isClickable =
    (companyId && jobPostingId) ||
    (adminCompany &&
      onAdminCalendarCompanyClick &&
      adminCompany.mapping_status !== 'pending' &&
      adminCompany.mapping_status !== 'processing');

  return (
    <div
      className={cn(
        badgeVariants({ type }),
        isClickable
          ? 'cursor-pointer hover:bg-gray-100 hover:shadow-sm hover:scale-105 transition-all duration-200 ease-in-out rounded-md px-1 py-0.5'
          : 'cursor-not-allowed opacity-60',
        className,
      )}
      onClick={handleClick}
      {...props}
    >
      <Typography
        variant="recruits"
        weight="bold"
        color={
          getStatusColor() === 'green'
            ? 'dabojob'
            : (getStatusColor() as 'dabojob' | 'red' | 'black' | 'gray' | 'yellow')
        }
        className={cn(isClickable ? 'transition-colors duration-200' : '')}
      >
        {getStatusText()}
      </Typography>
      {company && (
        <Typography
          variant="recruits"
          className={cn(
            'truncate max-w-[8rem]',
            isClickable ? 'transition-colors duration-200 hover:text-blue-600' : '',
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
