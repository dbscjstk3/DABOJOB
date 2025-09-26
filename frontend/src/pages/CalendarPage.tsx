import { useState } from 'react';
import { Calendar } from '../components/calendar/organisms/Calendar';

export default function CalendarPage() {
  // 현재 보이는 연/월 상태 (2025년 9월로 설정)
  const [viewDate, setViewDate] = useState(new Date(2025, 8, 1)); // 9월은 인덱스 8
  // 필터 상태
  const [employmentTypeFilter, setEmploymentTypeFilter] = useState<string[]>([]);
  const [jobCategoryFilter, setJobCategoryFilter] = useState<string[]>([]);

  return (
    <Calendar
      viewDate={viewDate}
      onViewDateChange={setViewDate}
      employmentTypeFilter={employmentTypeFilter}
      onEmploymentTypeChange={setEmploymentTypeFilter}
      jobCategoryFilter={jobCategoryFilter}
      onJobCategoryChange={setJobCategoryFilter}
    />
  );
}
