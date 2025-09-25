import { http, HttpResponse } from 'msw';
import { mockSummaryData } from './data/summary';
import { mockNewsData } from './data/news';
import { getAllJobPostings } from './jobPostings';
import { getFilteredJobPostings, createAutocompleteResponse } from './data/autocomplete';
import { searchJobPostings } from './data/jobPostings';
import type { NewsResponse, JobPostingResponse } from '@/lib/api';

export const handlers = [
  // 테스트용 관리자 로그인
  http.get('/api/auth/me', () => {
    console.log('🎭 MSW: 관리자 로그인 API 호출됨');
    return HttpResponse.json({
      id: 1,
      name: 'Admin',
      email: 'admin@example.com',
      role: 'ROLE_ADMIN',
      provider: 'local',
    });
  }),

  // Summary Detail API 목 핸들러
  http.get('/api/summary/:summaryId', ({ params }) => {
    const summaryId = params.summaryId as string;

    console.log(`🎭 MSW: Summary Detail API 호출됨 - ID: ${summaryId}`);

    // summaryId에 해당하는 목 데이터 반환
    const summaryData = mockSummaryData[summaryId];

    if (!summaryData) {
      console.log(`❌ MSW: Summary ID ${summaryId}에 해당하는 데이터가 없습니다.`);
      return new HttpResponse(null, {
        status: 404,
        statusText: 'Summary not found',
      });
    }

    console.log(`✅ MSW: ${summaryData.companyName} 데이터 반환`);

    // 실제 API처럼 약간의 지연 시뮬레이션 (선택사항)
    return HttpResponse.json(summaryData, {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }),

  // News API 목 핸들러
  http.get('/api/summary/:summaryId/news', ({ params }) => {
    const summaryId = params.summaryId as string;

    console.log(`🎭 MSW: News API 호출됨 - Summary ID: ${summaryId}`);

    const newsData = mockNewsData[summaryId];

    if (!newsData) {
      console.log(`❌ MSW: Summary ID ${summaryId}에 해당하는 뉴스 데이터가 없습니다.`);
      return HttpResponse.json([]);
    }

    console.log(`✅ MSW: ${newsData.length}개 뉴스 데이터 반환`);

    return HttpResponse.json(newsData, {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }),

  // 해시태그별 News API 목 핸들러
  http.get('/api/summary/:summaryId/news/:hashtagName', ({ params }) => {
    const summaryId = params.summaryId as string;
    const encodedHashtagName = params.hashtagName as string;
    const hashtagName = decodeURIComponent(encodedHashtagName);

    console.log(
      `🎭 MSW: 해시태그별 News API 호출됨 - Summary ID: ${summaryId}, Hashtag: ${hashtagName}`,
    );

    // 간단한 목 데이터 - 실제 백엔드가 알아서 필터링해주니까 여기서는 단순하게 처리
    const hashtagNewsMap: Record<string, NewsResponse[]> = {
      AI반도체: [
        {
          newsId: 1,
          summaryHashtagId: 10,
          newsUrl: 'https://news.example.com/samsung-hbm-production',
          newsTitle: '삼성전자, HBM3E 양산 본격화로 AI 반도체 시장 선도',
          newsContent:
            '삼성전자가 차세대 고대역폭 메모리 반도체인 HBM3E의 양산을 본격화하며 AI 반도체 시장에서의 리더십을 강화하고 있습니다. HBM3E는 기존 HBM3 대비 50% 향상된 성능을 제공하며, 엔비디아의 차세대 AI 가속기에 독점 공급될 예정입니다.',
          newsCreateDate: '2024-12-20',
        },
        {
          newsId: 2,
          summaryHashtagId: 11,
          newsUrl: 'https://news.example.com/samsung-ai-investment',
          newsTitle: '삼성전자, AI 반도체 개발에 3년간 100조원 투자 계획 발표',
          newsContent:
            '삼성전자가 인공지능 반도체 기술 개발과 생산 능력 확대를 위해 향후 3년간 100조원 규모의 대규모 투자를 단행한다고 발표했습니다.',
          newsCreateDate: '2024-12-19',
        },
      ],
      HBM: [
        {
          newsId: 3,
          summaryHashtagId: 10,
          newsUrl: 'https://news.example.com/samsung-hbm-production',
          newsTitle: '삼성전자, HBM3E 양산 본격화로 AI 반도체 시장 선도',
          newsContent:
            '삼성전자가 차세대 고대역폭 메모리 반도체인 HBM3E의 양산을 본격화하며 AI 반도체 시장에서의 리더십을 강화하고 있습니다. HBM3E는 기존 HBM3 대비 50% 향상된 성능을 제공하며, 엔비디아의 차세대 AI 가속기에 독점 공급될 예정입니다.',
          newsCreateDate: '2024-12-20',
        },
      ],
      투자: [
        {
          newsId: 4,
          summaryHashtagId: 11,
          newsUrl: 'https://news.example.com/samsung-ai-investment',
          newsTitle: '삼성전자, AI 반도체 개발에 3년간 100조원 투자 계획 발표',
          newsContent:
            '삼성전자가 인공지능 반도체 기술 개발과 생산 능력 확대를 위해 향후 3년간 100조원 규모의 대규모 투자를 단행한다고 발표했습니다. 이번 투자는 차세대 HBM, PIM 기술, 그리고 AI 전용 칩셋 개발에 집중될 예정입니다.',
          newsCreateDate: '2024-12-19',
        },
      ],
      // 필요한 태그별로 데이터 추가
    };

    const filteredNews = hashtagNewsMap[hashtagName] || [];

    if (filteredNews.length === 0) {
      console.log(`⚠️ MSW: 해시태그 '${hashtagName}'에 대한 뉴스가 없습니다. 빈 배열 반환`);
    } else {
      console.log(`✅ MSW: 해시태그 '${hashtagName}'에 대한 ${filteredNews.length}개 뉴스 반환`);
    }

    return HttpResponse.json(filteredNews, {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }),

  // 기간별 채용공고 조회 API 목 핸들러 (더 구체적인 패턴을 먼저 정의)
  http.get('/api/job-postings/calendar', ({ request }) => {
    const url = new URL(request.url);
    const startDate = url.searchParams.get('startDate');
    const endDate = url.searchParams.get('endDate');

    if (!startDate || !endDate) {
      return new HttpResponse(null, {
        status: 400,
        statusText: 'Bad Request - startDate and endDate are required',
      });
    }

    // 모든 채용공고 데이터 가져오기
    const allJobPostings = getAllJobPostings();

    // 날짜 범위 필터링
    const start = new Date(startDate);
    const end = new Date(endDate);

    const filteredJobPostings = allJobPostings.filter((posting) => {
      const postingDate = new Date(posting.postingDate);
      const deadlineDate = new Date(posting.deadlineDate);

      // 공고일 또는 마감일이 지정된 기간 내에 있는지 확인
      return (
        (postingDate >= start && postingDate <= end) ||
        (deadlineDate >= start && deadlineDate <= end)
      );
    });

    return HttpResponse.json(filteredJobPostings, {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }),

  // 자동완성 API 목 핸들러 (더 구체적인 패턴을 먼저 정의)
  http.get('/api/job-postings/suggestions', ({ request }) => {
    const url = new URL(request.url);
    const prefix = url.searchParams.get('prefix') || '';

    console.log(`🎭 MSW: 자동완성 API 호출됨 - prefix: "${prefix}"`);

    // 빈 prefix면 빈 결과 반환
    if (!prefix || prefix.trim().length === 0) {
      console.log('⚠️ MSW: prefix가 비어있음. 빈 결과 반환');
      const emptyResponse = createAutocompleteResponse([]);
      return HttpResponse.json(emptyResponse);
    }

    // prefix로 필터링된 채용공고 검색
    const filteredJobs = getFilteredJobPostings(prefix);
    const response = createAutocompleteResponse(filteredJobs);

    console.log(`✅ MSW: "${prefix}"로 검색한 결과 ${filteredJobs.length}개 채용공고 반환`);

    // 실제 API처럼 약간의 지연 추가 (100-300ms)
    const delay = Math.random() * 200 + 100;

    return new Promise((resolve) => {
      setTimeout(() => {
        resolve(
          HttpResponse.json(response, {
            status: 200,
            headers: {
              'Content-Type': 'application/json',
            },
          }),
        );
      }, delay);
    });
  }),

  // 검색 API 목 핸들러
  http.get('/api/job-postings', ({ request }) => {
    const url = new URL(request.url);
    const search = url.searchParams.get('search') || '';
    const page = parseInt(url.searchParams.get('page') || '0', 10);
    const size = parseInt(url.searchParams.get('size') || '20', 10);

    console.log(`🎭 MSW: 검색 API 호출됨 - search: "${search}", page: ${page}, size: ${size}`);

    // 검색어가 필수 파라미터
    if (!search) {
      console.log('❌ MSW: search 파라미터가 없습니다.');
      return new HttpResponse(null, {
        status: 400,
        statusText: 'Search parameter is required',
      });
    }

    // 검색 실행
    const searchResult = searchJobPostings(search, page, size);

    console.log(
      `✅ MSW: "${search}" 검색 결과 - 총 ${searchResult.totalElements}개 중 ${searchResult.numberOfElements}개 반환 (페이지: ${page + 1}/${searchResult.totalPages})`,
    );

    // 실제 API처럼 약간의 지연 추가
    const delay = Math.random() * 200 + 100;

    return new Promise((resolve) => {
      setTimeout(() => {
        resolve(
          HttpResponse.json(searchResult, {
            status: 200,
            headers: {
              'Content-Type': 'application/json',
            },
          }),
        );
      }, delay);
    });
  }),

  // 인기 공고 API 목 핸들러
  http.get('/api/job-postings/hot', () => {
    console.log('🎭 MSW: 인기 공고 API 호출됨');

    // 실시간 인기 공고 데이터
    const hotJobPostings = [
      {
        jobPostingId: '1',
        title: '백엔드 개발자 (Spring Boot)',
      },
      {
        jobPostingId: '2',
        title: '프론트엔드 개발자 (React)',
      },
      {
        jobPostingId: '3',
        title: '데이터 엔지니어',
      },
    ];

    console.log(
      `✅ MSW: 인기 공고 ${hotJobPostings.length}개 반환:`,
      hotJobPostings.map((job) => `${job.jobPostingId}: ${job.title}`).join(', '),
    );

    return HttpResponse.json(hotJobPostings, {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }),

  // JobPosting API 목 핸들러 (단수형) - 더 구체적인 패턴들 뒤에 배치
  http.get('/api/job-postings/:jobPostingId', ({ params }) => {
    const jobPostingId = params.jobPostingId as string;

    console.log(`🎭 MSW: JobPosting API 호출됨 - ID: ${jobPostingId}`);

    // 목 데이터 - 실제로는 jobPostingId에 따라 다른 데이터 반환
    const mockJobPostingData: Record<string, JobPostingResponse> = {
      '1': {
        jobPostingId: 1,
        companyId: 1,
        companyName: '삼성전자',
        companyType: '대기업',
        title: 'AI 반도체 개발 엔지니어',
        url: 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=123456',
        jobSectorName: '반도체 설계',
        jobSectorCategory: 'IT/하드웨어',
        careerInfo: 'senior',
        postingDate: '2024-12-15',
        deadlineDate: '2025-12-31',
      },
      '2': {
        jobPostingId: 17,
        companyId: 9002,
        companyName: '현대자동차',
        companyType: '대기업',
        title: '전기차 SW 개발자',
        url: 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=789012',
        jobSectorName: '소프트웨어 개발',
        jobSectorCategory: 'IT/소프트웨어',
        careerInfo: 'junior',
        postingDate: '2024-12-10',
        deadlineDate: '2024-12-25',
      },
      '3': {
        jobPostingId: 2,
        companyId: 2,
        companyName: 'LG전자',
        companyType: '대기업',
        title: '메모리 반도체 연구원',
        url: 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=345678',
        jobSectorName: '연구개발',
        jobSectorCategory: '연구/R&D',
        careerInfo: 'experienced',
        postingDate: '2024-12-20',
        deadlineDate: '2025-02-28',
      },
      '5': {
        jobPostingId: 5,
        companyId: 9005,
        companyName: '네이버',
        companyType: '대기업',
        title: '백엔드 개발자',
        url: 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=111111',
        jobSectorName: '백엔드 개발',
        jobSectorCategory: 'IT/서비스',
        careerInfo: 'experienced',
        postingDate: '2024-12-18',
        deadlineDate: '2025-01-15',
      },
      '7': {
        jobPostingId: 7,
        companyId: 9007,
        companyName: '카카오',
        companyType: '대기업',
        title: '프론트엔드 개발자',
        url: 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=222222',
        jobSectorName: '프론트엔드 개발',
        jobSectorCategory: 'IT/서비스',
        careerInfo: 'junior',
        postingDate: '2024-12-16',
        deadlineDate: '2025-01-10',
      },
      '8': {
        jobPostingId: 8,
        companyId: 9008,
        companyName: '토스',
        companyType: '중견기업',
        title: '풀스택 개발자',
        url: 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=333333',
        jobSectorName: '풀스택 개발',
        jobSectorCategory: 'IT/서비스',
        careerInfo: 'experienced',
        postingDate: '2024-12-14',
        deadlineDate: '2025-01-20',
      },
      '9': {
        jobPostingId: 9,
        companyId: 9009,
        companyName: '배달의민족',
        companyType: '중견기업',
        title: '모바일 앱 개발자',
        url: 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=444444',
        jobSectorName: '모바일 개발',
        jobSectorCategory: 'IT/서비스',
        careerInfo: 'senior',
        postingDate: '2024-12-12',
        deadlineDate: '2025-01-25',
      },
      '11': {
        jobPostingId: 11,
        companyId: 9011,
        companyName: '당근마켓',
        companyType: '중견기업',
        title: '데이터 엔지니어',
        url: 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=555555',
        jobSectorName: '데이터 엔지니어',
        jobSectorCategory: 'IT/서비스',
        careerInfo: 'experienced',
        postingDate: '2024-12-11',
        deadlineDate: '2025-01-30',
      },
      '12': {
        jobPostingId: 12,
        companyId: 9012,
        companyName: '쿠팡',
        companyType: '대기업',
        title: '클라우드 엔지니어',
        url: 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=666666',
        jobSectorName: '클라우드 엔지니어',
        jobSectorCategory: 'IT/서비스',
        careerInfo: 'senior',
        postingDate: '2024-12-09',
        deadlineDate: '2025-02-05',
      },
      '17': {
        jobPostingId: 3,
        companyId: 3,
        companyName: 'SK하이닉스',
        companyType: '대기업',
        title: 'AI 연구원',
        url: 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=777777',
        jobSectorName: 'AI 연구',
        jobSectorCategory: '연구/R&D',
        careerInfo: 'senior',
        postingDate: '2024-12-08',
        deadlineDate: '2025-02-10',
      },
    };

    const jobPostingData = mockJobPostingData[jobPostingId];

    if (!jobPostingData) {
      return new HttpResponse(null, {
        status: 404,
        statusText: 'Job Posting not found',
      });
    }

    return HttpResponse.json(jobPostingData, {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }),

  // 관리자용 채용공고 API 핸들러
  http.get('/api/admin/job-postings/calendar', ({ request }) => {
    const url = new URL(request.url);
    const year = url.searchParams.get('year');
    const month = url.searchParams.get('month');

    console.log(`🎭 MSW: 관리자용 채용공고 API 호출됨 - ${year}년 ${month}월`);

    // 관리자용 응답 데이터 (대기업 위주)
    const adminResponse = {
      year: parseInt(year || '2025'),
      month: parseInt(month || '9'),
      total_companies: 12,
      companies: [
        // 삼성 그룹
        {
          company_id: 1,
          company_name: '삼성전자(주)',
          mapping_status: 'verified',
          mapping_id: 1,
          first_posting_date: '2025-09-15',
          last_posting_date: '2025-09-25',
          job_count: 8,
          mapping_created_at: '2025-09-15T08:00:00',
          can_remap: false,
          job_postings: [
            {
              job_id: 1,
              job_title: '[삼성전자] 2025년 하반기 신입사원 공채',
              posting_date: '2025-09-15',
              application_deadline: '2025-10-15',
              job_url: 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=51900001',
            },
            {
              job_id: 2,
              job_title: '[삼성전자] 반도체 개발 엔지니어',
              posting_date: '2025-09-20',
              application_deadline: '2025-10-20',
              job_url: 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=51900002',
            },
            {
              job_id: 3,
              job_title: '[삼성전자] AI/ML 연구원',
              posting_date: '2025-09-25',
              application_deadline: '2025-10-25',
              job_url: 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=51900003',
            },
          ],
        },
        {
          company_id: 2,
          company_name: '삼성SDS(주)',
          mapping_status: 'verified',
          mapping_id: 2,
          first_posting_date: '2025-09-18',
          last_posting_date: '2025-09-28',
          job_count: 5,
          mapping_created_at: '2025-09-18T08:00:00',
          can_remap: false,
          job_postings: [
            {
              job_id: 4,
              job_title: '[삼성SDS] 클라우드 아키텍트',
              posting_date: '2025-09-18',
              application_deadline: '2025-10-18',
              job_url: 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=51900004',
            },
            {
              job_id: 5,
              job_title: '[삼성SDS] DevOps 엔지니어',
              posting_date: '2025-09-28',
              application_deadline: '2025-10-28',
              job_url: 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=51900005',
            },
          ],
        },
        // LG 그룹
        {
          company_id: 3,
          company_name: 'LG전자(주)',
          mapping_status: 'suggested',
          mapping_id: 3,
          first_posting_date: '2025-09-16',
          last_posting_date: '2025-09-26',
          job_count: 6,
          mapping_created_at: '2025-09-16T08:00:00',
          can_remap: true,
          job_postings: [
            {
              job_id: 6,
              job_title: '[LG전자] 2025년 하반기 신입사원 공채',
              posting_date: '2025-09-16',
              application_deadline: '2025-10-16',
              job_url: 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=51900006',
            },
            {
              job_id: 7,
              job_title: '[LG전자] 가전제품 개발 엔지니어',
              posting_date: '2025-09-26',
              application_deadline: '2025-10-26',
              job_url: 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=51900007',
            },
          ],
        },
        {
          company_id: 4,
          company_name: 'LG화학(주)',
          mapping_status: 'processing',
          mapping_id: 4,
          first_posting_date: '2025-09-19',
          last_posting_date: '2025-09-29',
          job_count: 4,
          mapping_created_at: '2025-09-19T08:00:00',
          can_remap: true,
          job_postings: [
            {
              job_id: 8,
              job_title: '[LG화학] 화학공학 연구원',
              posting_date: '2025-09-19',
              application_deadline: '2025-10-19',
              job_url: 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=51900008',
            },
          ],
        },
        // SK 그룹
        {
          company_id: 5,
          company_name: 'SK하이닉스(주)',
          mapping_status: 'verified',
          mapping_id: 5,
          first_posting_date: '2025-09-17',
          last_posting_date: '2025-09-27',
          job_count: 7,
          mapping_created_at: '2025-09-17T08:00:00',
          can_remap: false,
          job_postings: [
            {
              job_id: 9,
              job_title: '[SK하이닉스] 메모리 반도체 개발',
              posting_date: '2025-09-17',
              application_deadline: '2025-10-17',
              job_url: 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=51900009',
            },
            {
              job_id: 10,
              job_title: '[SK하이닉스] 공정 엔지니어',
              posting_date: '2025-09-27',
              application_deadline: '2025-10-27',
              job_url: 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=51900010',
            },
          ],
        },
        {
          company_id: 6,
          company_name: 'SK텔레콤(주)',
          mapping_status: 'failed',
          mapping_id: 6,
          first_posting_date: '2025-09-21',
          last_posting_date: '2025-09-21',
          job_count: 3,
          mapping_created_at: '2025-09-21T08:00:00',
          can_remap: true,
          job_postings: [
            {
              job_id: 11,
              job_title: '[SK텔레콤] 5G 네트워크 엔지니어',
              posting_date: '2025-09-21',
              application_deadline: '2025-10-21',
              job_url: 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=51900011',
            },
          ],
        },
        // 현대자동차 그룹
        {
          company_id: 7,
          company_name: '현대자동차(주)',
          mapping_status: 'verified',
          mapping_id: 7,
          first_posting_date: '2025-09-14',
          last_posting_date: '2025-09-24',
          job_count: 9,
          mapping_created_at: '2025-09-14T08:00:00',
          can_remap: false,
          job_postings: [
            {
              job_id: 12,
              job_title: '[현대자동차] 2025년 하반기 신입사원 공채',
              posting_date: '2025-09-14',
              application_deadline: '2025-10-14',
              job_url: 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=51900012',
            },
            {
              job_id: 13,
              job_title: '[현대자동차] 자율주행 SW 개발',
              posting_date: '2025-09-24',
              application_deadline: '2025-10-24',
              job_url: 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=51900013',
            },
          ],
        },
        {
          company_id: 8,
          company_name: '기아(주)',
          mapping_status: 'rejected',
          mapping_id: 8,
          first_posting_date: '2025-09-22',
          last_posting_date: '2025-09-22',
          job_count: 2,
          mapping_created_at: '2025-09-22T08:00:00',
          can_remap: true,
          job_postings: [
            {
              job_id: 14,
              job_title: '[기아] 전기차 개발 엔지니어',
              posting_date: '2025-09-22',
              application_deadline: '2025-10-22',
              job_url: 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=51900014',
            },
          ],
        },
        // 네이버
        {
          company_id: 9,
          company_name: '네이버(주)',
          mapping_status: 'verified',
          mapping_id: 9,
          first_posting_date: '2025-09-13',
          last_posting_date: '2025-09-23',
          job_count: 12,
          mapping_created_at: '2025-09-13T08:00:00',
          can_remap: false,
          job_postings: [
            {
              job_id: 15,
              job_title: '[네이버] 백엔드 개발자',
              posting_date: '2025-09-13',
              application_deadline: '2025-10-13',
              job_url: 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=51900015',
            },
            {
              job_id: 16,
              job_title: '[네이버] AI 연구원',
              posting_date: '2025-09-23',
              application_deadline: '2025-10-23',
              job_url: 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=51900016',
            },
          ],
        },
        // 카카오
        {
          company_id: 10,
          company_name: '카카오(주)',
          mapping_status: 'pending',
          mapping_id: 10,
          first_posting_date: '2025-09-20',
          last_posting_date: '2025-09-30',
          job_count: 8,
          mapping_created_at: '2025-09-20T08:00:00',
          can_remap: true,
          job_postings: [
            {
              job_id: 17,
              job_title: '[카카오] 프론트엔드 개발자',
              posting_date: '2025-09-20',
              application_deadline: '2025-10-20',
              job_url: 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=51900017',
            },
            {
              job_id: 18,
              job_title: '[카카오] 데이터 사이언티스트',
              posting_date: '2025-09-30',
              application_deadline: '2025-10-30',
              job_url: 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=51900018',
            },
          ],
        },
        // 쿠팡
        {
          company_id: 11,
          company_name: '쿠팡(주)',
          mapping_status: 'suggested',
          mapping_id: 11,
          first_posting_date: '2025-09-25',
          last_posting_date: '2025-09-25',
          job_count: 5,
          mapping_created_at: '2025-09-25T08:00:00',
          can_remap: true,
          job_postings: [
            {
              job_id: 19,
              job_title: '[쿠팡] 풀스택 개발자',
              posting_date: '2025-09-25',
              application_deadline: '2025-10-25',
              job_url: 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=51900019',
            },
          ],
        },
        // 배달의민족
        {
          company_id: 12,
          company_name: '우아한형제들(주)',
          mapping_status: 'processing',
          mapping_id: 12,
          first_posting_date: '2025-09-26',
          last_posting_date: '2025-09-26',
          job_count: 4,
          mapping_created_at: '2025-09-26T08:00:00',
          can_remap: true,
          job_postings: [
            {
              job_id: 20,
              job_title: '[배달의민족] 백엔드 개발자',
              posting_date: '2025-09-26',
              application_deadline: '2025-10-26',
              job_url: 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=51900020',
            },
          ],
        },
      ],
    };

    return HttpResponse.json(adminResponse, {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }),

  // 관리자용 작업 상태 조회 API 핸들러
  http.get('/api/admin/jobs/:jobId', ({ params }) => {
    const { jobId } = params;
    console.log(`🎭 MSW: 관리자용 작업 상태 조회 API 호출됨 - jobId: ${jobId}`);

    // 작업 상태 시뮬레이션 (jobId에 따라 다른 상태 반환)
    const statuses: ('processing' | 'finished' | 'completed')[] = [
      'processing',
      'finished',
      'completed',
    ];
    const status = statuses[parseInt(jobId as string) % 3];

    const response = {
      job_id: parseInt(jobId as string),
      status: status,
    };

    return HttpResponse.json(response, {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }),
];
