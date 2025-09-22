import React, { useState, useEffect, useMemo } from 'react';
import { CalendarGrid } from '../molecules/CalendarGrid';
import { CalendarHeader } from '../molecules/CalendarHeader';
import { FilterSection } from './FilterSection';
import { RecruitModal } from './RecruitModal';
import { cn } from '../../../lib/utils';
import { fetchJobPostingsByDateRange } from '../../../lib/api';
import type { JobPostingResponse } from '@/lib/api';

export interface CalendarProps {
  viewDate: Date;
  onViewDateChange: (date: Date) => void;
  employmentTypeFilter: string[];
  onEmploymentTypeChange: (values: string[]) => void;
  jobCategoryFilter: string[];
  onJobCategoryChange: (values: string[]) => void;
  companyTypeFilter: string[];
  onCompanyTypeChange: (values: string[]) => void;
  className?: string;
}

export const Calendar: React.FC<CalendarProps> = ({
  viewDate,
  onViewDateChange,
  employmentTypeFilter,
  onEmploymentTypeChange,
  jobCategoryFilter,
  onJobCategoryChange,
  companyTypeFilter,
  onCompanyTypeChange,
  className,
}) => {
  // 더보기(확장) 상태: 날짜 번호 Set
  const [expandedDays, setExpandedDays] = useState<Set<number>>(new Set());

  // 모달 상태
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedDay, setSelectedDay] = useState<number | null>(null);
  const [modalDate, setModalDate] = useState<Date>(new Date());

  // API 데이터 상태
  const [jobPostings, setJobPostings] = useState<JobPostingResponse[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 달력 기간 계산 (현재 월의 첫째 날과 마지막 날)
  const calendarDateRange = useMemo(() => {
    const year = viewDate.getFullYear();
    const month = viewDate.getMonth();
    const startDate = new Date(year, month, 1);
    const endDate = new Date(year, month + 1, 0);

    return {
      startDate: startDate.toISOString().split('T')[0], // YYYY-MM-DD 형식
      endDate: endDate.toISOString().split('T')[0],
    };
  }, [viewDate]);

  // API 호출
  useEffect(() => {
    const fetchJobPostings = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const data = await fetchJobPostingsByDateRange(
          calendarDateRange.startDate,
          calendarDateRange.endDate,
        );
        setJobPostings(data);
      } catch (err) {
        console.error('📅 Calendar: API 호출 실패', err);
        setError(err instanceof Error ? err.message : '채용공고를 불러오는데 실패했습니다.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchJobPostings();
  }, [calendarDateRange, viewDate]);

  // 날짜별로 그룹화된 채용공고 데이터
  const jobPostingsByDate = useMemo(() => {
    const grouped: Record<string, JobPostingResponse[]> = {};

    jobPostings.forEach((posting) => {
      // 공고일과 마감일 모두 처리
      // 시간대 문제를 방지하기 위해 로컬 날짜로 직접 파싱
      const postingDate = posting.postingDate; // 이미 YYYY-MM-DD 형식
      const deadlineDate = posting.deadlineDate; // 이미 YYYY-MM-DD 형식

      // 공고일
      if (!grouped[postingDate]) {
        grouped[postingDate] = [];
      }
      grouped[postingDate].push(posting);

      // 마감일 (공고일과 다른 경우에만)
      if (postingDate !== deadlineDate) {
        if (!grouped[deadlineDate]) {
          grouped[deadlineDate] = [];
        }
        grouped[deadlineDate].push(posting);
      }
    });

    return grouped;
  }, [jobPostings]);

  // 필터링된 공고 데이터 (공고일과 마감일 모두 포함)
  const getFilteredRecruits = (day: number): JobPostingResponse[] => {
    const year = viewDate.getFullYear();
    const month = viewDate.getMonth();
    // 시간대 문제를 방지하기 위해 로컬 날짜로 직접 생성
    const dateKey = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    const dayPostings = jobPostingsByDate[dateKey] || [];

    const filtered = dayPostings.filter((recruit) => {
      const employmentTypeMatch =
        employmentTypeFilter.length === 0 || employmentTypeFilter.includes(recruit.careerInfo);
      const jobCategoryMatch =
        jobCategoryFilter.length === 0 || jobCategoryFilter.includes(recruit.jobSectorCategory);
      const companyTypeMatch =
        companyTypeFilter.length === 0 || companyTypeFilter.includes(recruit.companyType);
      return employmentTypeMatch && jobCategoryMatch && companyTypeMatch;
    });

    return filtered;
  };

  // 모달 열기 함수
  const handleOpenModal = (day: number) => {
    setSelectedDay(day);
    const modalDate = new Date(viewDate.getFullYear(), viewDate.getMonth(), day);
    setModalDate(modalDate);
    setIsModalOpen(true);
  };

  // 모달 닫기 함수
  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedDay(null);
  };

  // 모달에서 날짜 변경 함수 (같은 달 내에서만)
  const handleModalDateChange = (date: Date) => {
    // 같은 달 내에서만 변경 허용
    if (date.getMonth() === viewDate.getMonth() && date.getFullYear() === viewDate.getFullYear()) {
      setModalDate(date);
      setSelectedDay(date.getDate());
    }
  };

  return (
    <div className={cn('w-full', className)}>
      {/* 필터 섹션 */}
      <FilterSection
        employmentTypeFilter={employmentTypeFilter}
        onEmploymentTypeChange={onEmploymentTypeChange}
        jobCategoryFilter={jobCategoryFilter}
        onJobCategoryChange={onJobCategoryChange}
        companyTypeFilter={companyTypeFilter}
        onCompanyTypeChange={onCompanyTypeChange}
      />

      <div className="p-6 w-full">
        {/* 달력 헤더 */}
        <CalendarHeader viewDate={viewDate} onViewDateChange={onViewDateChange} />

        {/* 로딩 상태 */}
        {isLoading && (
          <div className="flex justify-center items-center h-64">
            <div className="text-gray-500">채용공고를 불러오는 중...</div>
          </div>
        )}

        {/* 에러 상태 */}
        {error && (
          <div className="flex justify-center items-center h-64">
            <div className="text-red-500">에러: {error}</div>
          </div>
        )}

        {/* 달력 그리드 */}
        {!isLoading && !error && (
          <CalendarGrid
            viewDate={viewDate}
            getFilteredRecruits={getFilteredRecruits}
            expandedDays={expandedDays}
            onExpandedDaysChange={setExpandedDays}
            onOpenModal={handleOpenModal}
          />
        )}
      </div>

      {/* 채용 공고 모달 */}
      {selectedDay && (
        <RecruitModal
          isOpen={isModalOpen}
          onClose={handleCloseModal}
          recruits={getFilteredRecruits(selectedDay)}
          selectedDate={modalDate.getDate()}
          selectedMonth={modalDate.getMonth()}
          selectedYear={modalDate.getFullYear()}
          onDateChange={handleModalDateChange}
        />
      )}
    </div>
  );
};

export default Calendar;
