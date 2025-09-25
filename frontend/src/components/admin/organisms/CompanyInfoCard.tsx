import React, { useState } from 'react';
import { Typography } from '../../common/atoms/Typography';
import { type AdminCompany, type AdminJobPosting } from '../../../lib/api';
import { Divider } from '@/components/calendar-detail/atoms/Divider';

interface CompanyInfoCardProps {
  company: AdminCompany;
  jobPostings: AdminJobPosting[];
  jobPostingsCount: number;
}

export const CompanyInfoCard: React.FC<CompanyInfoCardProps> = ({
  company,
  jobPostings,
  jobPostingsCount,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const displayedJobs = isExpanded ? jobPostings : jobPostings.slice(0, 1);

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🏢</span>
          <Typography variant="title" weight="bold">
            {company.company_name}
          </Typography>
        </div>
        <Typography variant="default" color="gray">
          채용공고 {jobPostingsCount}건
        </Typography>
      </div>
      <Divider />
      <div className="my-3">
        <div className="flex flex-wrap gap-4">
          <div className="flex items-center gap-2">
            <Typography variant="default" color="gray">
              규모:
            </Typography>
            <Typography variant="default" weight="medium">
              {company.company_scale}
            </Typography>
          </div>
          <div className="flex items-center gap-2">
            <Typography variant="default" color="gray">
              그룹:
            </Typography>
            <Typography variant="default" weight="medium">
              {company.company_group}
            </Typography>
          </div>
          <div className="flex items-center gap-2">
            <Typography variant="default" color="gray">
              등록일:
            </Typography>
            <Typography variant="default" weight="medium">
              {new Date(company.created_at).toLocaleDateString('ko-KR')}
            </Typography>
          </div>
        </div>
      </div>
      <Divider />
      <div className="pt-3">
        <div className="flex items-center justify-between mb-3">
          <Typography variant="subtitle" weight="semibold">
            채용공고
          </Typography>
        </div>

        <div className="space-y-3">
          {displayedJobs.map((job) => (
            <div key={job.job_id} className="p-3 bg-gray-50 rounded-md">
              <Typography variant="default" weight="medium" className="mb-2">
                • {job.job_title}
              </Typography>
              <div className="flex flex-wrap gap-3 ml-3">
                <Typography variant="recruits" color="gray">
                  {job.career_info}
                </Typography>
                <Typography variant="recruits" color="gray">
                  {job.work_location}
                </Typography>
                <Typography variant="recruits" color="gray">
                  마감: {new Date(job.application_deadline).toLocaleDateString('ko-KR')}
                </Typography>
              </div>
            </div>
          ))}
        </div>

        {jobPostings.length > 1 && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="mt-3 text-slate-600 hover:text-blue-700 text-sm font-medium"
          >
            {isExpanded ? '접기' : `더보기 (${jobPostings.length - 1}개 더)`}
          </button>
        )}
      </div>
    </div>
  );
};
