import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from '@tanstack/react-router';
import { CalendarGrid } from '../molecules/CalendarGrid';
import { CalendarHeader } from '../molecules/CalendarHeader';
import { FilterSection } from './FilterSection';
import { RecruitModal } from './RecruitModal';
import { cn } from '../../../lib/utils';
import { fetchJobPostingsByDateRange, fetchAdminJobPostings } from '../../../lib/api';
import type { JobPostingResponse, AdminCompany } from '@/lib/api';
import { useAuthStore } from '@/stores/useAuthStore';
import { useLocation } from '@tanstack/react-router';

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
  const [adminCompanies, setAdminCompanies] = useState<AdminCompany[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 사용자 정보 가져오기
  const { user } = useAuthStore();
  const location = useLocation();
  const isAdminPath = location.pathname === '/admin';
  const isAdmin = isAdminPath || user?.role === 'admin' || user?.role === 'ROLE_ADMIN';

  // 디버깅용 로그
  console.log('🔍 Calendar Debug:', {
    user,
    isAdmin,
    userRole: user?.role,
    currentViewDate: viewDate,
    currentYear: viewDate.getFullYear(),
    currentMonth: viewDate.getMonth() + 1, // 1-based month
  });

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
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);

      try {
        if (isAdmin) {
          // 관리자용 API 호출
          console.log('🔍 관리자용 API 호출 중...');
          const year = viewDate.getFullYear();
          const month = viewDate.getMonth() + 1; // API는 1-based month를 사용
          const response = await fetchAdminJobPostings(year, month);
          console.log('🔍 관리자용 API 응답:', response);
          setAdminCompanies(response.companies);
          setJobPostings([]); // 일반 사용자용 데이터는 비움
        } else {
          // 일반 사용자용 API 호출
          console.log('🔍 일반 사용자용 API 호출 중...');
          const data = await fetchJobPostingsByDateRange(
            calendarDateRange.startDate,
            calendarDateRange.endDate,
          );
          setJobPostings(data);
          setAdminCompanies([]); // 관리자용 데이터는 비움
        }
      } catch (err) {
        console.error('📅 Calendar: API 호출 실패', err);
        setError(err instanceof Error ? err.message : '데이터를 불러오는데 실패했습니다.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [calendarDateRange, viewDate, isAdmin]);

  // 날짜별로 그룹화된 채용공고 데이터 (일반 사용자용)
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

  // 날짜별로 그룹화된 관리자용 회사 데이터
  const adminCompaniesByDate = useMemo(() => {
    const grouped: Record<string, AdminCompany[]> = {};

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

  // 필터링된 공고 데이터 (일반 사용자용)
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

  // 관리자용 회사 데이터 가져오기
  const getAdminCompaniesForDay = (day: number): AdminCompany[] => {
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
  const handleAdminCompanyClick = (company: AdminCompany) => {
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
            // 관리자용 props
            getAdminCompaniesForDay={getAdminCompaniesForDay}
            onAdminCompanyClick={handleAdminCompanyClick}
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
          // 관리자용 props
          adminCompanies={getAdminCompaniesForDay(selectedDay)}
          onAdminCompanyClick={handleAdminCompanyClick}
        />
      )}
    </div>
  );
};

export default Calendar;
