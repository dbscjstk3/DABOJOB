import React from 'react';
import { Typography } from '../../common/atoms/Typography';
import { type AdminMapping } from '../../../lib/api';

interface MappingStatusCardProps {
  mapping: AdminMapping;
}

export const MappingStatusCard: React.FC<MappingStatusCardProps> = ({ mapping }) => {
  const getStatusIcon = () => {
    switch (mapping.mapping_status) {
      case 'suggested':
      case 'rejected':
      case 'failed':
        return { icon: '❌', color: 'text-red-600', bg: 'bg-red-50' };
      default:
        return { icon: '❓', color: 'text-gray-600', bg: 'bg-gray-50' };
    }
  };

  const status = getStatusIcon();

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-4">
      <div className="flex items-center justify-between mb-4">
        <Typography variant="subtitle" weight="semibold">
          현재 매핑 상태
        </Typography>
        <div className={`flex items-center gap-2 px-3 py-1 rounded-full ${status.bg}`}>
          <span className="text-lg">{status.icon}</span>
          <Typography variant="default" weight="medium" className={status.color}>
            {mapping.mapping_status.toUpperCase()}
          </Typography>
        </div>
      </div>

      <div className="border-t pt-4 space-y-3">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Typography variant="recruits" color="gray" className="mb-1">
              DART 기업명
            </Typography>
            <Typography variant="default" weight="medium">
              {mapping.dart_corp_name}
            </Typography>
          </div>
          <div>
            <Typography variant="recruits" color="gray" className="mb-1">
              DART 기업코드
            </Typography>
            <Typography variant="default" weight="medium">
              {mapping.dart_corp_code}
            </Typography>
          </div>
          <div>
            <Typography variant="recruits" color="gray" className="mb-1">
              종목코드
            </Typography>
            <Typography variant="default" weight="medium">
              {mapping.dart_stock_code}
            </Typography>
          </div>
          <div>
            <Typography variant="recruits" color="gray" className="mb-1">
              신뢰도
            </Typography>
            <Typography variant="default" weight="medium">
              {mapping.confidence_score}%
            </Typography>
          </div>
        </div>

        {mapping.manual_notes && (
          <div className="mt-4 p-3 bg-red-50 rounded-md">
            <div className="flex items-start gap-2">
              <span className="text-red-500 mt-0.5">⚠️</span>
              <div>
                <Typography variant="default" weight="medium" color="red" className="mb-1">
                  오류 메시지
                </Typography>
                <Typography variant="recruits" className="text-red-700">
                  {mapping.manual_notes}
                </Typography>
              </div>
            </div>
          </div>
        )}

        {mapping.verified_at && (
          <div className="flex items-center gap-4 pt-2 text-sm text-gray-600">
            <Typography variant="recruits" color="gray">
              검증일: {new Date(mapping.verified_at).toLocaleDateString('ko-KR')}
            </Typography>
            {mapping.verified_by && (
              <Typography variant="recruits" color="gray">
                검증자: {mapping.verified_by}
              </Typography>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
