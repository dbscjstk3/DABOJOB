import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from '@tanstack/react-router';
import { CalendarGrid } from '../molecules/CalendarGrid';
import { CalendarHeader } from '../molecules/CalendarHeader';
import { FilterSection } from './FilterSection';
import { RecruitModal } from './RecruitModal';
import { cn } from '../../../lib/utils';
import { fetchAdminJobPostings } from '../../../lib/api';
import type { AdminCalendarCompany } from '@/lib/api';

export interface AdminCalendarProps {
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

export const AdminCalendar: React.FC<AdminCalendarProps> = ({
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

  // API 데이터 상태 (관리자용만)
  const [adminCompanies, setAdminCompanies] = useState<AdminCalendarCompany[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 디버깅용 로그
  console.log('🔍 AdminCalendar Debug:', {
    currentViewDate: viewDate,
    currentYear: viewDate.getFullYear(),
    currentMonth: viewDate.getMonth() + 1, // 1-based month
  });

  // 관리자용 API 호출
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);

      try {
        console.log('🔍 관리자용 API 호출 중...');
        const year = viewDate.getFullYear();
        const month = viewDate.getMonth() + 1; // API는 1-based month를 사용
        const response = await fetchAdminJobPostings(year, month);
        console.log('🔍 관리자용 API 응답:', response);
        setAdminCompanies(response.companies);
      } catch (err) {
        console.error('📅 AdminCalendar: API 호출 실패', err);
        setError(err instanceof Error ? err.message : '데이터를 불러오는데 실패했습니다.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [viewDate]);

  // 날짜별로 그룹화된 관리자용 회사 데이터
  const adminCompaniesByDate = useMemo(() => {
    const grouped: Record<string, AdminCalendarCompany[]> = {};

    console.log('🔍 관리자용 회사 데이터 그룹화:', adminCompanies);

    adminCompanies.forEach((company) => {
      // 첫 공고일과 마지막 공고일 모두 처리
      const firstPostingDate = company.first_posting_date;
      const lastPostingDate = company.last_posting_date;

      console.log(`🔍 회사 ${company.company_name}: ${firstPostingDate} ~ ${lastPostingDate}`);

      // 첫 공고일
      if (!grouped[firstPostingDate]) {
        grouped[firstPostingDate] = [];
      }
      grouped[firstPostingDate].push(company);

      // 마지막 공고일 (첫 공고일과 다른 경우에만)
      if (firstPostingDate !== lastPostingDate) {
        if (!grouped[lastPostingDate]) {
          grouped[lastPostingDate] = [];
        }
        grouped[lastPostingDate].push(company);
      }
    });

    console.log('🔍 그룹화된 관리자용 회사 데이터:', grouped);
    return grouped;
  }, [adminCompanies]);

  // 일반 사용자용 필터링 함수 (빈 배열 반환 - 관리자는 일반 공고를 보지 않음)
  const getFilteredRecruits = (): never[] => {
    return [];
  };

  // 관리자용 회사 데이터 가져오기
  const getAdminCompaniesForDay = (day: number): AdminCalendarCompany[] => {
    const year = viewDate.getFullYear();
    const month = viewDate.getMonth();
    const dateKey = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    const companies = adminCompaniesByDate[dateKey] || [];
    console.log(`🔍 ${dateKey} 관리자용 회사 데이터:`, companies);
    return companies;
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

  // 관리자용 회사 클릭 핸들러
  const navigate = useNavigate();
  const handleAdminCalendarCompanyClick = (company: AdminCalendarCompany) => {
    console.log('Admin company clicked:', company);

    switch (company.mapping_status) {
      case 'pending':
      case 'processing':
        // 매핑 대기 중이거나 처리 중인 경우 - 클릭 불가
        alert('아직 매핑이 완료되지 않았습니다. 잠시 후 다시 시도해주세요.');
        break;

      case 'suggested':
      case 'rejected':
      case 'failed':
        // 관리자 수동 매핑 페이지로 이동
        navigate({
          to: '/admin/mapping/$companyId',
          params: { companyId: company.company_id.toString() },
        });
        break;

      case 'verified':
        // verified 상태는 정상적으로 클릭 가능 (모달 열기)
        // 이 경우는 RecruitModal에서 처리됨
        break;

      default:
        console.warn('Unknown mapping status:', company.mapping_status);
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
            <div className="text-gray-500">관리자 데이터를 불러오는 중...</div>
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
            // 관리자용 props
            getAdminCompaniesForDay={getAdminCompaniesForDay}
            onAdminCalendarCompanyClick={handleAdminCalendarCompanyClick}
          />
        )}
      </div>

      {/* 채용 공고 모달 (관리자용) */}
      {selectedDay && (
        <RecruitModal
          isOpen={isModalOpen}
          onClose={handleCloseModal}
          recruits={[]} // 관리자는 일반 공고를 보지 않음
          selectedDate={modalDate.getDate()}
          selectedMonth={modalDate.getMonth()}
          selectedYear={modalDate.getFullYear()}
          onDateChange={handleModalDateChange}
          // 관리자용 props
          adminCompanies={getAdminCompaniesForDay(selectedDay)}
          onAdminCalendarCompanyClick={handleAdminCalendarCompanyClick}
        />
      )}
    </div>
  );
};

export default AdminCalendar;
