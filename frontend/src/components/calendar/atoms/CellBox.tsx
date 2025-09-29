import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../../lib/utils';
import { RecruitBadge } from './RecruitBadge';
import { Typography } from '../../common/atoms/Typography';
import type { JobPostingResponse, AdminCalendarCompany } from '@/lib/api';
import { groupCompaniesByGroup } from '@/lib/companyUtils';

const cellBoxVariants = cva('flex flex-col border-t border-daboja-default p-2 h-20 md:h-72', {
  variants: {
    tone: {
      default: 'bg-white',
      muted: 'bg-slate-100 text-slate-500',
    },
    today: {
      false: '',
      true: 'bg-slate-50',
    },
    interactive: {
      false: '',
      true: 'cursor-pointer hover:bg-slate-100 hover:shadow-sm',
    },
  },
  defaultVariants: {
    tone: 'default',
    today: false,
    interactive: true,
  },
});

export interface CellBoxProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cellBoxVariants> {
  /** 추가 CSS 클래스 */
  className?: string;
  /** 자식 요소 */
  children?: React.ReactNode;
  /** 날짜 */
  day?: number | null;
  /** 요일 (0: 일요일, 1: 월요일, ..., 6: 토요일) */
  dayOfWeek?: number;
  /** 공고 데이터 */
  recruits?: JobPostingResponse[];
  /** 관리자용 회사 데이터 */
  adminCompanies?: AdminCalendarCompany[];
  /** 확장 상태 */
  isExpanded?: boolean;
  /** 확장 토글 함수 */
  onToggleExpanded?: (day: number) => void;
  /** 모달 열기 함수 */
  onOpenModal?: (day: number) => void;
  /** 관리자용 회사 클릭 핸들러 */
  onAdminCalendarCompanyClick?: (company: AdminCalendarCompany) => void;
  /** 숨김 상태 */
  isHidden?: boolean;
}

/**
 * CellBox 컴포넌트 - cva 기반
 */
export const CellBox: React.FC<CellBoxProps> = ({
  tone,
  today,
  interactive,
  className,
  children,
  day,
  dayOfWeek,
  recruits = [],
  adminCompanies = [],
  isExpanded = false,
  onToggleExpanded: _onToggleExpanded,
  onOpenModal,
  onAdminCalendarCompanyClick,
  isHidden = false,
  ...props
}) => {
  // 빈 칸은 border만 유지하고 내용 숨김
  if (isHidden) {
    return <div className="border-t border-daboja-default h-20 md:h-72" {...props} />;
  }

  return (
    <div
      tabIndex={0}
      role="gridcell"
      className={cn(cellBoxVariants({ tone, today, interactive }), className)}
      onClick={() => {
        if (day && (recruits.length > 0 || adminCompanies.length > 0)) {
          onOpenModal?.(day);
        }
      }}
      style={{
        cursor: day && (recruits.length > 0 || adminCompanies.length > 0) ? 'pointer' : 'default',
      }}
      {...props}
    >
      {day && (
        <div className="flex flex-col h-full mt-2 gap-2">
          <div className="flex items-center justify-start">
            {today ? (
              <div className="w-7 h-7 bg-[#099AEE] rounded-full flex items-center justify-center">
                <Typography variant="dayNumber" color="white" weight="bold" align="center">
                  {day}
                </Typography>
              </div>
            ) : (
              <div className="w-7 h-7 rounded-full flex items-center justify-center">
                <Typography
                  variant="dayNumber"
                  color={
                    tone === 'default'
                      ? dayOfWeek === 0
                        ? 'red'
                        : dayOfWeek === 6
                          ? 'dabojob'
                          : 'black'
                      : 'gray'
                  }
                  weight="regular"
                  align="center"
                >
                  {day}
                </Typography>
              </div>
            )}
          </div>
          {/* 공고 배지 렌더링 */}
          <div className="flex flex-col gap-1">
            {/* 일반 사용자용 공고 표시 */}
            {recruits.length > 0 && (
              <>
                {/* 모바일: 개수만 표시, 데스크톱: 개별 공고 표시 */}
                <div className="block md:hidden">
                  <div className="flex items-center justify-center">
                    <div className="bg-blue-100 text-black text-xs px-2 py-1 rounded-full font-medium">
                      +{recruits.length}
                    </div>
                  </div>
                </div>

                {/* 데스크톱: 개별 공고 표시 */}
                <div className="hidden md:flex md:flex-col md:gap-1">
                  {(isExpanded ? recruits : recruits.slice(0, 8)).map((item, idx) => {
                    // 공고가 해당 날짜에 공고일인지 마감일인지 구분
                    const postingDate = new Date(item.postingDate);
                    const isPostingDate = postingDate.getDate() === day;

                    return (
                      <RecruitBadge
                        key={idx}
                        type={isPostingDate ? 'start' : 'end'}
                        company={item.companyName}
                        companyId={item.companyId}
                        jobPostingId={item.jobPostingId}
                      />
                    );
                  })}
                  {recruits.length > 8 && (
                    <button
                      type="button"
                      className="text-left"
                      onClick={(e) => {
                        e.stopPropagation();
                        onOpenModal?.(day);
                      }}
                    >
                      <Typography variant="recruits" color="gray">
                        +{recruits.length - 8} 더보기
                      </Typography>
                    </button>
                  )}
                </div>
              </>
            )}

            {/* 관리자용 회사 표시 */}
            {adminCompanies.length > 0 && (
              <>
                {/* 회사들을 그룹별로 분류 */}
                {(() => {
                  const groupedCompanies = groupCompaniesByGroup(adminCompanies);
                  const groupEntries = Object.entries(groupedCompanies);

                  return (
                    <>
                      {/* 모바일: 그룹 개수만 표시 */}
                      <div className="block md:hidden">
                        <div className="flex items-center justify-center">
                          <div className="bg-green-100 text-black text-xs px-2 py-1 rounded-full font-medium">
                            +{groupEntries.length}
                          </div>
                        </div>
                      </div>

                      {/* 데스크톱: 개별 그룹 표시 */}
                      <div className="hidden md:flex md:flex-col md:gap-1">
                        {groupEntries
                          .slice(0, isExpanded ? undefined : 8)
                          .map(([groupName, groupCompanies], idx) => {
                            // 그룹의 첫 번째 회사를 대표로 사용
                            const representativeCompany = groupCompanies[0];
                            const totalJobs = groupCompanies.reduce(
                              (sum, company) => sum + company.job_count,
                              0,
                            );

                            // 그룹의 매핑 상태 결정 (우선순위: failed > rejected > suggested > processing > pending > verified)
                            const getGroupMappingStatus = () => {
                              if (
                                groupCompanies.some(
                                  (company) => company.mapping_status === 'failed',
                                )
                              )
                                return 'failed';
                              if (
                                groupCompanies.some(
                                  (company) => company.mapping_status === 'rejected',
                                )
                              )
                                return 'rejected';
                              if (
                                groupCompanies.some(
                                  (company) => company.mapping_status === 'suggested',
                                )
                              )
                                return 'suggested';
                              if (
                                groupCompanies.some(
                                  (company) => company.mapping_status === 'processing',
                                )
                              )
                                return 'processing';
                              if (
                                groupCompanies.some(
                                  (company) => company.mapping_status === 'pending',
                                )
                              )
                                return 'pending';
                              return 'verified';
                            };

                            return (
                              <div key={idx} className="flex items-center gap-1">
                                <RecruitBadge
                                  type={getGroupMappingStatus()}
                                  company={groupName}
                                  adminCompany={{
                                    ...representativeCompany,
                                    company_name: groupName,
                                    job_count: totalJobs,
                                  }}
                                  onAdminCalendarCompanyClick={onAdminCalendarCompanyClick}
                                />
                                {groupCompanies.length > 1 && (
                                  <span className="text-xs text-gray-500">
                                    +{groupCompanies.length - 1}
                                  </span>
                                )}
                              </div>
                            );
                          })}
                        {groupEntries.length > 8 && (
                          <button
                            type="button"
                            className="text-left"
                            onClick={(e) => {
                              e.stopPropagation();
                              onOpenModal?.(day);
                            }}
                          >
                            <Typography variant="recruits" color="gray">
                              +{groupEntries.length - 8} 더보기
                            </Typography>
                          </button>
                        )}
                      </div>
                    </>
                  );
                })()}
              </>
            )}
          </div>
        </div>
      )}
      {children}
    </div>
  );
};

export default CellBox;
