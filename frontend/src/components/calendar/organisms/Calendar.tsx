import React, { useState } from 'react';
import { CalendarGrid } from '../molecules/CalendarGrid';
import { CalendarHeader } from '../molecules/CalendarHeader';
import { FilterSection } from './FilterSection';
import { cn } from '../../../lib/utils';

export interface CalendarProps {
  viewDate: Date;
  onViewDateChange: (date: Date) => void;
  employmentTypeFilter: string[];
  onEmploymentTypeChange: (values: string[]) => void;
  jobCategoryFilter: string[];
  onJobCategoryChange: (values: string[]) => void;
  className?: string;
}

// 샘플 공고 데이터 (날짜별 시작/종료 이벤트)
const recruitMap: Record<
  number,
  {
    type: 'start' | 'end';
    company: string;
    employmentType: string;
    jobCategory: string;
  }[]
> = {
  2: [
    {
      type: 'start',
      company: '삼성전자',
      employmentType: 'full-time',
      jobCategory: 'development',
    },
    {
      type: 'start',
      company: '삼성SDS',
      employmentType: 'full-time',
      jobCategory: 'development',
    },
    { type: 'start', company: '삼성생명', employmentType: 'contract', jobCategory: 'finance' },
    {
      type: 'start',
      company: '삼성SDI',
      employmentType: 'full-time',
      jobCategory: 'development',
    },
    {
      type: 'start',
      company: '삼성디스플레이',
      employmentType: 'full-time',
      jobCategory: 'design',
    },
    { type: 'start', company: '삼성물산', employmentType: 'contract', jobCategory: 'management' },
    { type: 'start', company: '삼성화재', employmentType: 'full-time', jobCategory: 'finance' },
    {
      type: 'start',
      company: '삼성바이오',
      employmentType: 'full-time',
      jobCategory: 'development',
    },
    {
      type: 'start',
      company: '삼성전기',
      employmentType: 'full-time',
      jobCategory: 'development',
    },
    {
      type: 'start',
      company: '삼성중공업',
      employmentType: 'full-time',
      jobCategory: 'development',
    },
    { type: 'start', company: '삼성카드', employmentType: 'full-time', jobCategory: 'finance' },
    { type: 'start', company: '삼성증권', employmentType: 'full-time', jobCategory: 'finance' },
    { type: 'start', company: '삼성E&A', employmentType: 'contract', jobCategory: 'development' },
    {
      type: 'end',
      company: '현대자동차',
      employmentType: 'full-time',
      jobCategory: 'development',
    },
  ],
  3: [
    { type: 'start', company: 'KB국민은행', employmentType: 'full-time', jobCategory: 'finance' },
  ],
  4: [{ type: 'end', company: '멀티캠퍼스', employmentType: 'contract', jobCategory: 'education' }],
  5: [
    {
      type: 'start',
      company: '비바리퍼블리카',
      employmentType: 'full-time',
      jobCategory: 'development',
    },
    { type: 'start', company: '카카오', employmentType: 'full-time', jobCategory: 'development' },
  ],
};

export const Calendar: React.FC<CalendarProps> = ({
  viewDate,
  onViewDateChange,
  employmentTypeFilter,
  onEmploymentTypeChange,
  jobCategoryFilter,
  onJobCategoryChange,
  className,
}) => {
  // 더보기(확장) 상태: 날짜 번호 Set
  const [expandedDays, setExpandedDays] = useState<Set<number>>(new Set());

  // 필터링된 공고 데이터
  const getFilteredRecruits = (day: number) => {
    const recruits = recruitMap[day] || [];
    return recruits.filter((recruit) => {
      const employmentTypeMatch =
        employmentTypeFilter.length === 0 || employmentTypeFilter.includes(recruit.employmentType);
      const jobCategoryMatch =
        jobCategoryFilter.length === 0 || jobCategoryFilter.includes(recruit.jobCategory);
      return employmentTypeMatch && jobCategoryMatch;
    });
  };

  return (
    <div className={cn('w-full', className)}>
      {/* 필터 섹션 */}
      <FilterSection
        employmentTypeFilter={employmentTypeFilter}
        onEmploymentTypeChange={onEmploymentTypeChange}
        jobCategoryFilter={jobCategoryFilter}
        onJobCategoryChange={onJobCategoryChange}
      />

      <div className="p-6 w-full">
        {/* 달력 헤더 */}
        <CalendarHeader viewDate={viewDate} onViewDateChange={onViewDateChange} />

        {/* 달력 그리드 */}
        <CalendarGrid
          viewDate={viewDate}
          getFilteredRecruits={getFilteredRecruits}
          expandedDays={expandedDays}
          onExpandedDaysChange={setExpandedDays}
        />
      </div>
    </div>
  );
};

export default Calendar;
