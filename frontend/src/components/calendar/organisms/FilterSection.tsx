import React from 'react';
import { FilterDropdown, type FilterOption } from '../molecules/FilterDropdown';
import { cn } from '../../../lib/utils';

export interface FilterSectionProps {
  employmentTypeFilter: string[];
  onEmploymentTypeChange: (values: string[]) => void;
  jobCategoryFilter: string[];
  onJobCategoryChange: (values: string[]) => void;
  className?: string;
}

// 채용 형태 옵션
const employmentTypeOptions: FilterOption[] = [
  { value: 'new', label: '신입' },
  { value: 'used-new', label: '경력' },
  { value: 'intern', label: '인턴' },
];

// 직무 카테고리 옵션
const jobCategoryOptions: FilterOption[] = [
  { value: 'development', label: '개발' },
  { value: 'design', label: '디자인' },
  { value: 'marketing', label: '마케팅' },
  { value: 'sales', label: '영업' },
  { value: 'hr', label: '인사' },
  { value: 'finance', label: '재무' },
  { value: 'management', label: '경영' },
  { value: 'customer-service', label: '고객서비스' },
  { value: 'operations', label: '운영' },
  { value: 'data', label: '데이터' },
  { value: 'security', label: '보안' },
  { value: 'qa', label: 'QA' },
];

export const FilterSection: React.FC<FilterSectionProps> = ({
  employmentTypeFilter,
  onEmploymentTypeChange,
  jobCategoryFilter,
  onJobCategoryChange,
  className,
}) => {
  return (
    <div className={cn('w-full min-h-16 bg-white border-b border-gray-200 py-4', className)}>
      <div className="px-12">
        <div className="flex items-center">
          {/* 왼쪽 필터들 */}
          <div className="flex items-center gap-6 flex-wrap">
            <FilterDropdown
              label="채용형태"
              options={employmentTypeOptions}
              selectedValues={employmentTypeFilter}
              onSelectionChange={onEmploymentTypeChange}
              placeholder="신입"
              className="w-48 min-w-48"
            />

            <FilterDropdown
              label="직무"
              options={jobCategoryOptions}
              selectedValues={jobCategoryFilter}
              onSelectionChange={onJobCategoryChange}
              placeholder="개발자"
              className="w-48 min-w-48"
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default FilterSection;
