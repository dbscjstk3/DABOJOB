import React, { useState } from 'react';
import { CalendarGrid } from '../molecules/CalendarGrid';
import { CalendarHeader } from '../molecules/CalendarHeader';
import { FilterSection } from './FilterSection';
import { RecruitModal } from './RecruitModal';
import { cn } from '../../../lib/utils';
import { getRecruitsByDate, recruitMap } from '../../../mocks/recruitData';

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
  // 더보기(확장) 상태: 날짜 번호 Set
  const [expandedDays, setExpandedDays] = useState<Set<number>>(new Set());

  // 모달 상태
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedDay, setSelectedDay] = useState<number | null>(null);
  const [modalDate, setModalDate] = useState<Date>(new Date());

  // 필터링된 공고 데이터 (공고일과 마감일 모두 포함)
  const getFilteredRecruits = (day: number) => {
    const allRecruits = getRecruitsByDate(day);

    // 마감일이 해당 날짜인 공고들도 추가로 가져오기
    const expirationRecruits = Object.values(recruitMap)
      .flat()
      .filter((recruit) => {
        const expirationDate = new Date(recruit.expiration_date);
        return (
          expirationDate.getDate() === day &&
          expirationDate.getMonth() === viewDate.getMonth() &&
          expirationDate.getFullYear() === viewDate.getFullYear()
        );
      });

    // 공고일과 마감일 공고를 합치고 중복 제거
    const combinedRecruits = [...allRecruits, ...expirationRecruits];
    const uniqueRecruits = combinedRecruits.filter(
      (recruit, index, self) => index === self.findIndex((r) => r.job_id === recruit.job_id),
    );

    return uniqueRecruits.filter((recruit) => {
      const employmentTypeMatch =
        employmentTypeFilter.length === 0 || employmentTypeFilter.includes(recruit.job_type.name);
      const jobCategoryMatch =
        jobCategoryFilter.length === 0 || jobCategoryFilter.includes(recruit.job_code.name);
      return employmentTypeMatch && jobCategoryMatch;
    });
  };

  // 모달 열기 함수
  const handleOpenModal = (day: number) => {
    setSelectedDay(day);
    setModalDate(new Date(viewDate.getFullYear(), viewDate.getMonth(), day));
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
          onOpenModal={handleOpenModal}
        />
      </div>

      {/* 채용 공고 모달 */}
      {selectedDay && (
        <RecruitModal
          isOpen={isModalOpen}
          onClose={handleCloseModal}
          recruits={getFilteredRecruits(modalDate.getDate())}
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
