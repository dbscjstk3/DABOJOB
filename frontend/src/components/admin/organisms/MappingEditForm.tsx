import React, { useState } from 'react';
import { Typography } from '../../common/atoms/Typography';
import { Button } from '../../common/atoms/Button';
import { type AdminMappingUpdateRequest } from '../../../lib/api';
import { Divider } from '@/components/calendar-detail/atoms/Divider';

interface MappingEditFormProps {
  initialValues?: Partial<AdminMappingUpdateRequest>;
  onSubmit: (data: AdminMappingUpdateRequest) => void;
  isLoading?: boolean;
}

export const MappingEditForm: React.FC<MappingEditFormProps> = ({
  initialValues,
  onSubmit,
  isLoading = false,
}) => {
  const [formData, setFormData] = useState<AdminMappingUpdateRequest>({
    dart_corp_name: initialValues?.dart_corp_name || '',
    dart_corp_code: initialValues?.dart_corp_code || '',
    dart_stock_code: initialValues?.dart_stock_code || '',
    manual_notes: initialValues?.manual_notes || '',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center gap-2 mb-4">
        <Typography variant="subtitle" weight="semibold">
          DART 정보 수정
        </Typography>
      </div>
      <Divider />

      <form onSubmit={handleSubmit} className="space-y-4 mt-3">
        <div>
          <Typography variant="default" weight="medium" className="mb-2">
            DART 기업명 <span className="text-red-500">*</span>
          </Typography>
          <input
            type="text"
            name="dart_corp_name"
            value={formData.dart_corp_name}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="예: 삼성전자"
            disabled={isLoading}
            required
          />
        </div>

        <div>
          <Typography variant="default" weight="medium" className="mb-2">
            DART 기업코드 <span className="text-red-500">*</span>
          </Typography>
          <input
            type="text"
            name="dart_corp_code"
            value={formData.dart_corp_code}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="예: 00126380"
            disabled={isLoading}
            required
          />
        </div>

        <div>
          <Typography variant="default" weight="medium" className="mb-2">
            종목코드
          </Typography>
          <input
            type="text"
            name="dart_stock_code"
            value={formData.dart_stock_code}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="예: 005930"
            disabled={isLoading}
            required
          />
        </div>

        <div>
          <Typography variant="default" weight="medium" className="mb-2">
            관리자 메모
          </Typography>
          <textarea
            name="manual_notes"
            value={formData.manual_notes}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[80px]"
            placeholder="추가 메모사항을 입력하세요"
            disabled={isLoading}
          />
        </div>

        <div className="flex gap-3 pt-2">
          <Button className="w-full" type="submit" variant="contained" disabled={isLoading}>
            {isLoading ? '처리 중...' : '매핑 업데이트'}
          </Button>
        </div>
      </form>
    </div>
  );
};
