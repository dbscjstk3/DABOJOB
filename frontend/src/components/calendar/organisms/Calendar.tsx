import React from 'react';
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

export const Calendar: React.FC<CalendarProps> = ({
  viewDate,
  onViewDateChange,
  employmentTypeFilter,
  onEmploymentTypeChange,
  jobCategoryFilter,
  onJobCategoryChange,
  className,
}) => {
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
          employmentTypeFilter={employmentTypeFilter}
          jobCategoryFilter={jobCategoryFilter}
        />
      </div>
    </div>
  );
};

export default Calendar;
