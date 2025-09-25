import { useState } from 'react';
import { AdminCalendar } from '@/components/calendar/organisms/AdminCalendar';

export default function AdminCalendarPage() {
  // 달력 상태 관리
  const [viewDate, setViewDate] = useState(new Date());

  // 필터 상태 관리
  const [employmentTypeFilter, setEmploymentTypeFilter] = useState<string[]>([]);
  const [jobCategoryFilter, setJobCategoryFilter] = useState<string[]>([]);
  const [companyTypeFilter, setCompanyTypeFilter] = useState<string[]>([]);

  return (
    <AdminCalendar
      viewDate={viewDate}
      onViewDateChange={setViewDate}
      employmentTypeFilter={employmentTypeFilter}
      onEmploymentTypeChange={setEmploymentTypeFilter}
      jobCategoryFilter={jobCategoryFilter}
      onJobCategoryChange={setJobCategoryFilter}
      companyTypeFilter={companyTypeFilter}
      onCompanyTypeChange={setCompanyTypeFilter}
    />
  );
}
