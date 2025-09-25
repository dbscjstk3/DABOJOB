import React, { useState } from 'react';
import { useParams, useSearch } from '@tanstack/react-router';
import { useAdminMappingData, useAdminMappingUpdate } from '../lib/hooks';
import { Typography } from '../components/common/atoms/Typography';
import { CompanyInfoCard } from '../components/admin/organisms/CompanyInfoCard';
import { MappingStatusCard } from '../components/admin/organisms/MappingStatusCard';
import { MappingEditForm } from '../components/admin/organisms/MappingEditForm';
import { MappingResultCard } from '../components/admin/organisms/MappingResultCard';
import { type AdminMappingUpdateRequest } from '../lib/api';
import { type MappingResultStatus } from '../types/mapping.types';

export const AdminMappingPage: React.FC = () => {
  // TanStack Router의 useParams와 useSearch 사용
  const { companyId } = useParams({ from: '/admin/mapping/$companyId' });
  const search = useSearch({ from: '/admin/mapping/$companyId' }) as {
    year?: number;
    month?: number;
  };
  const [resultStatus, setResultStatus] = useState<MappingResultStatus>('idle');

  // 현재 날짜를 기본값으로 사용
  const year = search.year || new Date().getFullYear();
  const month = search.month || new Date().getMonth() + 1;

  // 커스텀 훅 사용
  const {
    data: pageData,
    isLoading,
    error,
  } = useAdminMappingData(companyId ? Number(companyId) : undefined, year, month);

  const updateMappingMutation = useAdminMappingUpdate(Number(companyId || 0), year, month);

  const handleMappingUpdate = async (data: AdminMappingUpdateRequest) => {
    if (companyId) {
      setResultStatus('loading');

      try {
        await updateMappingMutation.mutateAsync(data);
        setResultStatus('success');
      } catch (error) {
        setResultStatus('error');
        console.error('Failed to update mapping:', error);
      }
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <Typography variant="default" color="gray">
            데이터를 불러오는 중...
          </Typography>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-red-50 p-6 rounded-lg">
          <Typography variant="default" color="red">
            오류: {error.message}
          </Typography>
        </div>
      </div>
    );
  }

  if (!pageData) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto p-6">
        <div className="mb-6">
          <Typography variant="title" weight="bold">
            기업 DART 매핑 관리
          </Typography>
        </div>

        <CompanyInfoCard
          company={pageData.company}
          jobPostings={pageData.job_postings}
          jobPostingsCount={pageData.job_postings_count}
        />

        <MappingStatusCard mapping={pageData.mapping} />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <MappingEditForm
            initialValues={{
              dart_corp_name: pageData.mapping.dart_corp_name,
              dart_corp_code: pageData.mapping.dart_corp_code,
              dart_stock_code: pageData.mapping.dart_stock_code,
              manual_notes: '',
            }}
            onSubmit={handleMappingUpdate}
            isLoading={resultStatus === 'loading' || updateMappingMutation.isPending}
          />

          <MappingResultCard
            status={resultStatus}
            result={updateMappingMutation.data}
            estimatedTime={600}
          />
        </div>

        {updateMappingMutation.error && (
          <div className="mt-4 bg-red-50 p-4 rounded-lg">
            <Typography variant="default" color="red">
              {updateMappingMutation.error.message}
            </Typography>
          </div>
        )}
      </div>
    </div>
  );
};
