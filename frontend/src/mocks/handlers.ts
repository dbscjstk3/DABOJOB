import { http, HttpResponse } from 'msw';
import { mockSummaryData } from './data/summary';
import { mockNewsData } from './data/news';
import { getAllJobPostings } from './data/jobPostingsForDetailPage';
import { getFilteredJobPostings, createAutocompleteResponse } from './data/autocomplete';
import { searchJobPostings } from './data/jobPostings';
import { mockCompanyMappings, mockMappingUpdateResponse } from './data/adminMapping';
import type { NewsResponse, AdminMappingUpdateRequest } from '@/lib/api';

export const handlers = [
  // Summary Detail API 목 핸들러
  http.get('/api/summaries/:summaryId', ({ params }) => {
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
  http.get('/api/summaries/:summaryId/news', ({ params }) => {
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
  http.get('/api/summaries/:summaryId/news/:hashtagName', ({ params }) => {
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
          url: 'https://news.example.com/samsung-hbm-production',
          title: '삼성전자, HBM3E 양산 본격화로 AI 반도체 시장 선도',
          content:
            '삼성전자가 차세대 고대역폭 메모리 반도체인 HBM3E의 양산을 본격화하며 AI 반도체 시장에서의 리더십을 강화하고 있습니다. HBM3E는 기존 HBM3 대비 50% 향상된 성능을 제공하며, 엔비디아의 차세대 AI 가속기에 독점 공급될 예정입니다.',
          postingDate: '2024-12-20',
        },
        {
          newsId: 2,
          summaryHashtagId: 11,
          url: 'https://news.example.com/samsung-ai-investment',
          title: '삼성전자, AI 반도체 개발에 3년간 100조원 투자 계획 발표',
          content:
            '삼성전자가 인공지능 반도체 기술 개발과 생산 능력 확대를 위해 향후 3년간 100조원 규모의 대규모 투자를 단행한다고 발표했습니다.',
          postingDate: '2024-12-19',
        },
      ],
      HBM: [
        {
          newsId: 3,
          summaryHashtagId: 10,
          url: 'https://news.example.com/samsung-hbm-production',
          title: '삼성전자, HBM3E 양산 본격화로 AI 반도체 시장 선도',
          content:
            '삼성전자가 차세대 고대역폭 메모리 반도체인 HBM3E의 양산을 본격화하며 AI 반도체 시장에서의 리더십을 강화하고 있습니다. HBM3E는 기존 HBM3 대비 50% 향상된 성능을 제공하며, 엔비디아의 차세대 AI 가속기에 독점 공급될 예정입니다.',
          postingDate: '2024-12-20',
        },
      ],
      투자: [
        {
          newsId: 4,
          summaryHashtagId: 11,
          url: 'https://news.example.com/samsung-ai-investment',
          title: '삼성전자, AI 반도체 개발에 3년간 100조원 투자 계획 발표',
          content:
            '삼성전자가 인공지능 반도체 기술 개발과 생산 능력 확대를 위해 향후 3년간 100조원 규모의 대규모 투자를 단행한다고 발표했습니다. 이번 투자는 차세대 HBM, PIM 기술, 그리고 AI 전용 칩셋 개발에 집중될 예정입니다.',
          postingDate: '2024-12-19',
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

    // jobPostings.ts에서 데이터 가져오기
    const allJobPostings = getAllJobPostings();
    const jobPostingData = allJobPostings.find(
      (posting) => posting.jobPostingId === parseInt(jobPostingId),
    );

    if (!jobPostingData) {
      console.log(`❌ MSW: Job Posting ID ${jobPostingId}를 찾을 수 없습니다.`);
      return new HttpResponse(null, {
        status: 404,
        statusText: 'Job Posting not found',
      });
    }

    console.log(`✅ MSW: ${jobPostingData.companyName} - ${jobPostingData.title} 데이터 반환`);

    return HttpResponse.json(jobPostingData, {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }),

  // Admin Mapping API 목 핸들러 - 조회
  http.get('/api/admin/calendar/companies/:companyId', ({ params, request }) => {
    const companyId = params.companyId as string;
    const url = new URL(request.url);
    const year = url.searchParams.get('year');
    const month = url.searchParams.get('month');

    console.log(
      `🎭 MSW: Admin Mapping API 호출됨 - Company ID: ${companyId}, Year: ${year}, Month: ${month}`,
    );

    const mappingData = mockCompanyMappings[companyId];

    if (!mappingData) {
      console.log(`❌ MSW: Company ID ${companyId}에 해당하는 매핑 데이터가 없습니다.`);
      return new HttpResponse(null, {
        status: 404,
        statusText: 'Company mapping not found',
      });
    }

    // year, month가 요청되면 period 정보 업데이트
    if (year && month) {
      mappingData.period.year = parseInt(year);
      mappingData.period.month = parseInt(month);
    }

    console.log(`✅ MSW: ${mappingData.company.company_name} 매핑 데이터 반환`);

    return HttpResponse.json(mappingData, {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }),

  // Admin Mapping API 목 핸들러 - 업데이트 (remap)
  // 절대 URL과 상대 URL 모두 캐치
  http.post('*/api/admin/calendar/companies/:companyId/remap', async ({ params, request }) => {
    const companyId = params.companyId as string;
    const body = (await request.json()) as AdminMappingUpdateRequest;

    console.log(`🎭 MSW: Admin Mapping Update API 호출됨 - Company ID: ${companyId}`, body);

    // 10분 후를 시뮬레이션하기 위해 약간의 지연 추가 (실제로는 10분 기다리지 않고 2초만)
    await new Promise((resolve) => setTimeout(resolve, 2000));

    // 요청받은 데이터로 응답 커스터마이즈
    const customResponse = {
      ...mockMappingUpdateResponse,
      mapping: {
        ...mockMappingUpdateResponse.mapping,
        company_id: parseInt(companyId),
        dart_corp_name: body.dart_corp_name || mockMappingUpdateResponse.mapping.dart_corp_name,
        dart_corp_code: body.dart_corp_code || mockMappingUpdateResponse.mapping.dart_corp_code,
        dart_stock_code: body.dart_stock_code || mockMappingUpdateResponse.mapping.dart_stock_code,
      },
    };

    console.log(`✅ MSW: 매핑 업데이트 성공 응답 반환`);

    return HttpResponse.json(customResponse, {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }),
];
