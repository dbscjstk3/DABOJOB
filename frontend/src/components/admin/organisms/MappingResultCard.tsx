import React, { useEffect, useState } from 'react';
import { Typography } from '../../common/atoms/Typography';
import { type AdminMappingUpdateResponse } from '../../../lib/api';
import { type MappingResultStatus } from '../../../types/mapping.types';

interface MappingResultCardProps {
  status: MappingResultStatus;
  result?: AdminMappingUpdateResponse;
  estimatedTime?: number;
}

const SkeletonLine: React.FC<{ width?: string }> = ({ width = 'w-full' }) => (
  <div className={`h-4 bg-gray-300 rounded animate-pulse ${width}`} />
);

export const MappingResultCard: React.FC<MappingResultCardProps> = ({
  status,
  result,
  estimatedTime = 600,
}) => {
  const [progress, setProgress] = useState(0);
  const [elapsedTime, setElapsedTime] = useState(0);

  useEffect(() => {
    if (status === 'loading' && estimatedTime > 0) {
      const interval = setInterval(() => {
        setElapsedTime((prev) => {
          const next = prev + 1;
          setProgress((next / estimatedTime) * 100);
          return next;
        });
      }, 1000);

      return () => clearInterval(interval);
    } else {
      setElapsedTime(0);
      setProgress(0);
    }
  }, [status, estimatedTime]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}분 ${secs}초`;
  };

  const renderContent = () => {
    switch (status) {
      case 'idle':
        return (
          <div className="flex flex-col items-center justify-center h-48 bg-gray-100 rounded-md">
            <span className="text-3xl mb-2">💤</span>
            <Typography variant="default" color="gray">
              대기 중...
            </Typography>
            <Typography variant="recruits" color="gray" className="mt-1">
              매핑 업데이트 버튼을 눌러주세요
            </Typography>
          </div>
        );

      case 'loading':
        return (
          <div className="space-y-4">
            <div className="space-y-3">
              <SkeletonLine width="w-3/4" />
              <SkeletonLine width="w-1/2" />
              <SkeletonLine width="w-5/6" />
              <SkeletonLine width="w-2/3" />
            </div>

            <div className="pt-4 border-t">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xl animate-spin">⏳</span>
                <Typography variant="default" weight="medium">
                  처리 중...
                </Typography>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-1000"
                  style={{ width: `${Math.min(progress, 95)}%` }}
                />
              </div>
              <Typography variant="recruits" color="gray">
                경과 시간: {formatTime(elapsedTime)} / 예상: 약 10분
              </Typography>
            </div>
          </div>
        );

      case 'success':
        return result ? (
          <div className="space-y-3">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-2xl">✅</span>
              <Typography variant="default" weight="semibold" className="text-green-600">
                매핑 성공
              </Typography>
            </div>

            <div className="bg-green-50 p-3 rounded-md mb-3">
              <Typography variant="default" className="text-green-800">
                {result.message}
              </Typography>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between">
                <Typography variant="recruits" color="gray">
                  변경 내용:
                </Typography>
                <Typography variant="recruits" weight="medium">
                  {result.mapping.company_name} → {result.mapping.dart_corp_name}
                </Typography>
              </div>
              <div className="flex justify-between">
                <Typography variant="recruits" color="gray">
                  DART 코드:
                </Typography>
                <Typography variant="recruits" weight="medium">
                  {result.mapping.dart_corp_code}
                </Typography>
              </div>
              <div className="flex justify-between">
                <Typography variant="recruits" color="gray">
                  종목코드:
                </Typography>
                <Typography variant="recruits" weight="medium">
                  {result.mapping.dart_stock_code}
                </Typography>
              </div>
              <div className="flex justify-between">
                <Typography variant="recruits" color="gray">
                  적용 공고:
                </Typography>
                <Typography variant="recruits" weight="medium">
                  {result.mapping.job_count}개
                </Typography>
              </div>
              <div className="flex justify-between">
                <Typography variant="recruits" color="gray">
                  신뢰도:
                </Typography>
                <Typography variant="recruits" weight="medium">
                  {result.mapping.confidence_score}%
                </Typography>
              </div>
            </div>

            <div className="pt-3 border-t">
              <Typography variant="recruits" color="gray">
                완료: {new Date(result.mapping.verified_at).toLocaleString('ko-KR')}
              </Typography>
            </div>
          </div>
        ) : null;

      case 'error':
        return (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <span className="text-2xl">❌</span>
              <Typography variant="default" weight="semibold" color="red">
                매핑 실패
              </Typography>
            </div>
            <div className="bg-red-50 p-3 rounded-md">
              <Typography variant="default" className="text-red-700">
                매핑 처리 중 오류가 발생했습니다. 다시 시도해주세요.
              </Typography>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center gap-2 mb-4">
        {/* <span className="text-xl">📊</span> */}
        <Typography variant="subtitle" weight="semibold">
          매핑 결과
        </Typography>
      </div>

      <div className="border-t pt-4">{renderContent()}</div>
    </div>
  );
};
