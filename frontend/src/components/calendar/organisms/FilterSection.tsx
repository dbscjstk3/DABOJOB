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
  { value: 'IT/서비스', label: 'IT/서비스' },
  { value: 'IT/플랫폼', label: 'IT/플랫폼' },
  { value: 'IT/보안', label: 'IT/보안' },
  { value: '제조/모빌리티', label: '제조/모빌리티' },
  { value: 'IT/커머스', label: 'IT/커머스' },
  { value: '게임/엔터', label: '게임/엔터' },
  { value: '바이오/헬스', label: '바이오/헬스' },
  { value: '금융/핀테크', label: '금융/핀테크' },
  { value: '물류/유통', label: '물류/유통' },
  { value: '미디어/콘텐츠', label: '미디어/콘텐츠' },
  { value: 'R&D/연구', label: 'R&D/연구' },
  { value: 'IT/인프라', label: 'IT/인프라' },
  { value: 'AI/ML', label: 'AI/ML' },
  { value: '에너지/산업', label: '에너지/산업' },
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
              placeholder="채용형태 선택"
              className="w-30 min-w-40"
            />

            <FilterDropdown
              label="직무"
              options={jobCategoryOptions}
              selectedValues={jobCategoryFilter}
              onSelectionChange={onJobCategoryChange}
              placeholder="직무 선택"
              className="w-30 min-w-40"
            />

            <FilterDropdown
              label="기업형태"
              options={companyTypeOptions}
              selectedValues={companyTypeFilter}
              onSelectionChange={onCompanyTypeChange}
              placeholder="기업형태 선택"
              className="w-30 min-w-40"
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default FilterSection;
