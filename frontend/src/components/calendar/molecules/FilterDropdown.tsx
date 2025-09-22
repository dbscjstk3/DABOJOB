import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, X } from 'lucide-react';
import { cn } from '../../../lib/utils';
import { Typography } from '../../common/atoms/Typography';

export interface FilterOption {
  value: string;
  label: string;
}

export interface FilterDropdownProps {
  label: string;
  options: FilterOption[];
  selectedValues: string[];
  onSelectionChange: (values: string[]) => void;
  placeholder?: string;
  className?: string;
  multiple?: boolean;
}

export const FilterDropdown: React.FC<FilterDropdownProps> = ({
  label,
  options,
  selectedValues,
  onSelectionChange,
  placeholder = '선택하세요',
  className,
  multiple = true,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // 외부 클릭 시 드롭다운 닫기
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleOptionClick = (optionValue: string) => {
    if (multiple) {
      const newValues = selectedValues.includes(optionValue)
        ? selectedValues.filter((value) => value !== optionValue)
        : [...selectedValues, optionValue];
      onSelectionChange(newValues);
    } else {
      onSelectionChange([optionValue]);
      setIsOpen(false);
    }
  };

  const handleRemoveValue = (valueToRemove: string) => {
    onSelectionChange(selectedValues.filter((value) => value !== valueToRemove));
  };

  const handleClearAll = () => {
    onSelectionChange([]);
  };

  const getDisplayText = () => {
    if (selectedValues.length === 0) {
      return placeholder;
    }
    if (selectedValues.length === 1) {
      const option = options.find((opt) => opt.value === selectedValues[0]);
      return option?.label || selectedValues[0];
    }
    return `${selectedValues.length}개 선택됨`;
  };

  return (
    <div className={cn('relative', className)} ref={dropdownRef}>
      <button
        type="button"
        onClick={() => {
          console.log('FilterDropdown clicked, current isOpen:', isOpen);
          setIsOpen(!isOpen);
        }}
        className={cn(
          'w-full h-8 px-3 py-1 text-left bg-transparent border-none',
          'flex items-center gap-1',
        )}
      >
        <div className="flex items-center gap-2 min-w-0 flex-1">
          <Typography
            variant="default"
            color="black"
            weight="semibold"
            align="left"
            className="whitespace-nowrap text-xs sm:text-sm"
          >
            {label}
          </Typography>
          <Typography
            variant="default"
            color="gray"
            align="left"
            className="truncate text-xs sm:text-sm"
          >
            {getDisplayText()}
          </Typography>
        </div>
        <ChevronDown
          className={cn(
            'h-3 w-3 sm:h-4 sm:w-4 text-gray-400 transition-transform duration-200 flex-shrink-0 ml-auto',
            isOpen && 'rotate-180',
          )}
        />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-60 overflow-y-auto">
          {/* 선택된 항목들 표시 */}
          {selectedValues.length > 0 && multiple && (
            <div className="p-2 border-b border-gray-700">
              <div className="flex items-center justify-between mb-2">
                <Typography variant="default" color="gray" className="text-xs">
                  선택된 항목
                </Typography>
                <button
                  type="button"
                  onClick={handleClearAll}
                  className="text-xs text-red-400 hover:text-red-300"
                >
                  모두 지우기
                </button>
              </div>
              <div className="flex flex-wrap gap-1">
                {selectedValues.map((value) => {
                  const option = options.find((opt) => opt.value === value);
                  return (
                    <span
                      key={value}
                      className="inline-flex items-center gap-1 px-2 py-1 bg-daboja-default text-gray-200 text-xs rounded-full"
                    >
                      {option?.label || value}
                      <button
                        type="button"
                        onClick={() => handleRemoveValue(value)}
                        className="hover:text-gray-400"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  );
                })}
              </div>
            </div>
          )}

          {/* 옵션 목록 */}
          <div className="py-1">
            {options.map((option) => {
              const isSelected = selectedValues.includes(option.value);
              return (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => handleOptionClick(option.value)}
                  className={cn(
                    'w-full px-4 py-2 text-left hover:bg-gray-100 flex items-center justify-between',
                  )}
                >
                  <Typography variant="default" color="black" className="truncate">
                    {option.label}
                  </Typography>
                  {isSelected && multiple && <div className="w-2 h-2 bg-white rounded-full" />}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default FilterDropdown;
