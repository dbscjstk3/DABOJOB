import React from 'react';
import { FilterDropdown, type FilterOption } from '../molecules/FilterDropdown';
import { cn } from '../../../lib/utils';

export interface FilterSectionProps {
  employmentTypeFilter: string[];
  onEmploymentTypeChange: (values: string[]) => void;
  jobCategoryFilter: string[];
  onJobCategoryChange: (values: string[]) => void;
  companyTypeFilter: string[];
  onCompanyTypeChange: (values: string[]) => void;
  className?: string;
}

// 채용 형태 옵션
const employmentTypeOptions: FilterOption[] = [
  { value: '신입', label: '신입' },
  { value: '경력', label: '경력' },
  { value: '인턴', label: '인턴' },
];

// 직무 카테고리 옵션
const jobCategoryOptions: FilterOption[] = [
  { value: '개발', label: '개발' },
  { value: '디자인', label: '디자인' },
  { value: '마케팅', label: '마케팅' },
  { value: '영업', label: '영업' },
  { value: '인사', label: '인사' },
  { value: '재무', label: '재무' },
  { value: '경영', label: '경영' },
  { value: '고객서비스', label: '고객서비스' },
  { value: '운영', label: '운영' },
  { value: '데이터', label: '데이터' },
  { value: '보안', label: '보안' },
  { value: 'QA', label: 'QA' },
];

// 기업형태 옵션
const companyTypeOptions: FilterOption[] = [
  { value: '대기업', label: '대기업' },
  { value: '중견기업', label: '중견기업' },
  { value: '중소기업', label: '중소기업' },
];

export const FilterSection: React.FC<FilterSectionProps> = ({
  employmentTypeFilter,
  onEmploymentTypeChange,
  jobCategoryFilter,
  onJobCategoryChange,
  companyTypeFilter,
  onCompanyTypeChange,
  className,
}) => {
  return (
    <div className={cn('w-full min-h-16 bg-white border-b border-gray-200 py-4', className)}>
      <div className="px-12">
        <div className="flex items-center">
          {/* 왼쪽 필터들 */}
          <div className="flex items-center gap-1 flex-wrap">
            <FilterDropdown
              label="채용형태"
              options={employmentTypeOptions}
              selectedValues={employmentTypeFilter}
              onSelectionChange={onEmploymentTypeChange}
              placeholder="신입"
              className="w-30 min-w-40"
            />

            <FilterDropdown
              label="직무"
              options={jobCategoryOptions}
              selectedValues={jobCategoryFilter}
              onSelectionChange={onJobCategoryChange}
              placeholder="개발자"
              className="w-30 min-w-40"
            />

            <FilterDropdown
              label="기업형태"
              options={companyTypeOptions}
              selectedValues={companyTypeFilter}
              onSelectionChange={onCompanyTypeChange}
              placeholder="대기업"
              className="w-30 min-w-40"
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default FilterSection;
