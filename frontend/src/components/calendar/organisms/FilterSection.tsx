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

// 채용 형태 옵션 (백엔드 응답과 동일한 한글 값으로 통일)
const employmentTypeOptions: FilterOption[] = [
  { value: '신입', label: '신입' },
  { value: '경력', label: '경력' },
  { value: '시니어', label: '시니어' },
];

// 직무 카테고리 옵션 (실제 달력 데이터에 맞춤)
const jobCategoryOptions: FilterOption[] = [
  { value: '구조설계', label: '구조설계' },
  { value: '금융 플랫폼', label: '금융 플랫폼' },
  { value: '콘텐츠기획/제작', label: '콘텐츠기획/제작' },
  { value: '문서작성', label: '문서작성' },
  { value: '정보보안', label: '정보보안' },
  { value: '소재/무역/물류', label: '소재/무역/물류' },
  { value: '기계설비', label: '기계설비' },
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
      <div className="px-4 sm:px-8 lg:px-12">
        <div className="flex items-center">
          {/* 왼쪽 필터들 */}
          <div className="flex items-center gap-1">
            <FilterDropdown
              label="채용형태"
              options={employmentTypeOptions}
              selectedValues={employmentTypeFilter}
              onSelectionChange={onEmploymentTypeChange}
              placeholder="신입"
              className="w-28 min-w-28 sm:w-32 sm:min-w-32 lg:w-36 lg:min-w-36"
            />

            <FilterDropdown
              label="직무"
              options={jobCategoryOptions}
              selectedValues={jobCategoryFilter}
              onSelectionChange={onJobCategoryChange}
              placeholder="구조설계"
              className="w-32 min-w-32 sm:w-36 sm:min-w-36 lg:w-40 lg:min-w-40"
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default FilterSection;
