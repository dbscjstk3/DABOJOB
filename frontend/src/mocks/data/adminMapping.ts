import { type AdminMappingResponse, type AdminMappingUpdateResponse } from '../../lib/api';

// Admin Mapping 목 데이터
export const mockAdminMappingData: AdminMappingResponse = {
  company: {
    company_id: 1,
    company_name: '(주)연우',
    company_url: null,
    company_scale: '코스닥',
    company_group: '콜마홀딩스그룹',
    created_at: '2025-09-24T08:21:45',
  },
  mapping: {
    mapping_id: 1,
    mapping_status: 'failed' as const,
    dart_corp_name: '(주)연우',
    dart_corp_code: '002760',
    dart_stock_code: '115960',
    confidence_score: 100,
    gpt_response:
      "{'dart_corp_name': '(주)연우', 'dart_corp_code': '002760', 'dart_stock_code': '115960', 'confidence': 100, 'notes': '정확히 일치'}",
    manual_notes: 'DART parsing failed - no content extracted (2025-09-24 17:22:33)',
    processed_at: null,
    verified_at: null,
    verified_by: null,
    can_remap: true,
  },
  period: {
    year: 2025,
    month: 9,
    first_posting_date: '2025-09-24',
    last_posting_date: '2025-09-24',
  },
  job_postings: [
    {
      job_id: 1,
      job_title: '[HK연우]2025 하반기 콜마그룹 대졸신입 공채',
      work_location: '인천전체',
      salary_info: '면접 후 협의',
      career_info: '신입 · 정규직 외',
      education_requirement: '대학교(4년)↑',
      posting_date: '2025-09-24',
      application_deadline: '2025-10-13',
      job_url:
        'https://www.saramin.co.kr/zf_user/jobs/relay/view?view_type=public-recruit&rec_idx=51908493',
      status: 'active',
      is_hot: false,
      registration_info: '6시간 전 등록',
    },
    {
      job_id: 5,
      job_title: '[HK연우]2025 하반기 콜마그룹 대졸신입 공채(해외영업)',
      work_location: '인천전체',
      salary_info: '면접 후 협의',
      career_info: '신입 · 정규직 외',
      education_requirement: '대학교(4년)↑',
      posting_date: '2025-09-24',
      application_deadline: '2025-10-13',
      job_url:
        'https://www.saramin.co.kr/zf_user/jobs/relay/view?view_type=public-recruit&rec_idx=51907168',
      status: 'active',
      is_hot: false,
      registration_info: '8시간 전 등록',
    },
    {
      job_id: 10,
      job_title: '[HK연우]2025 하반기 콜마그룹 대졸신입 공채(생산관리)',
      work_location: '인천전체',
      salary_info: '면접 후 협의',
      career_info: '신입 · 정규직 외',
      education_requirement: '대학교(4년)↑',
      posting_date: '2025-09-24',
      application_deadline: '2025-10-13',
      job_url:
        'https://www.saramin.co.kr/zf_user/jobs/relay/view?view_type=public-recruit&rec_idx=51906234',
      status: 'active',
      is_hot: false,
      registration_info: '9시간 전 등록',
    },
    {
      job_id: 15,
      job_title: '[HK연우]2025 하반기 콜마그룹 대졸신입 공채(품질관리)',
      work_location: '인천전체',
      salary_info: '면접 후 협의',
      career_info: '신입 · 정규직 외',
      education_requirement: '대학교(4년)↑',
      posting_date: '2025-09-24',
      application_deadline: '2025-10-13',
      job_url:
        'https://www.saramin.co.kr/zf_user/jobs/relay/view?view_type=public-recruit&rec_idx=51905987',
      status: 'active',
      is_hot: false,
      registration_info: '10시간 전 등록',
    },
  ],
  job_postings_count: 4,
};

// 매핑 업데이트 성공 응답 목 데이터
export const mockMappingUpdateResponse: AdminMappingUpdateResponse = {
  status: 'success' as const,
  message: '(주)연우 → 연우 매핑이 완료되었습니다 (4개 채용공고에 적용)',
  mapping: {
    company_id: 1,
    company_name: '(주)연우',
    dart_corp_name: '연우',
    dart_corp_code: 'A115960',
    dart_stock_code: 'A115960',
    job_count: 4,
    confidence_score: 100,
    verified_by: 'admin_manual',
    verified_at: '2025-09-25T01:07:52.096501',
  },
};

// 다른 회사들의 목 데이터 (필요시 추가)
export const mockCompanyMappings: Record<string, AdminMappingResponse> = {
  '1': mockAdminMappingData,
  '2': {
    company: {
      company_id: 2,
      company_name: '삼성전자',
      company_url: 'https://www.samsung.com',
      company_scale: '코스피',
      company_group: '삼성그룹',
      created_at: '2025-09-20T10:30:00',
    },
    mapping: {
      mapping_id: 2,
      mapping_status: 'rejected' as const,
      dart_corp_name: '삼성전자',
      dart_corp_code: '00126380',
      dart_stock_code: '005930',
      confidence_score: 100,
      gpt_response:
        "{'dart_corp_name': '삼성전자', 'dart_corp_code': '00126380', 'dart_stock_code': '005930', 'confidence': 100}",
      manual_notes: '',
      processed_at: '2025-09-20T10:35:00',
      verified_at: '2025-09-20T10:35:00',
      verified_by: 'system',
      can_remap: false,
    },
    period: {
      year: 2025,
      month: 9,
      first_posting_date: '2025-09-01',
      last_posting_date: '2025-09-25',
    },
    job_postings: [
      {
        job_id: 100,
        job_title: '삼성전자 DS부문 반도체 설계 엔지니어 채용',
        work_location: '경기 화성시',
        salary_info: '회사 내규',
        career_info: '경력 3년 이상',
        education_requirement: '대학교(4년)↑',
        posting_date: '2025-09-20',
        application_deadline: '2025-10-20',
        job_url: 'https://www.saramin.co.kr/example',
        status: 'active',
        is_hot: true,
        registration_info: '2일 전 등록',
      },
    ],
    job_postings_count: 1,
  },
};
