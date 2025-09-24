import { http, HttpResponse } from 'msw';
import { mockSummaryData } from './data/summary';
import { mockNewsData } from './data/news';
import { getAllJobPostings } from './jobPostings';
import { getFilteredJobPostings, createAutocompleteResponse } from './data/autocomplete';
import { searchJobPostings } from './data/jobPostings';
import type { NewsResponse, JobPostingResponse } from '@/lib/api';

export const handlers = [
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

    // 최근 7일간 많이 클릭된 공고들의 jobPostingId 배열
    const hotJobPostingIds = [1, 5, 8, 2, 12, 7, 3, 11, 9, 17];

    console.log(
      `✅ MSW: 인기 공고 ID ${hotJobPostingIds.length}개 반환: [${hotJobPostingIds.join(', ')}]`,
    );

    return HttpResponse.json(hotJobPostingIds, {
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
        careerInfo: '경력 3년 이상',
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
        careerInfo: '신입',
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
        careerInfo: '경력무관',
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
        careerInfo: '경력 2년 이상',
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
        careerInfo: '신입',
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
        careerInfo: '경력 1년 이상',
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
        careerInfo: '경력 3년 이상',
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
        careerInfo: '경력 2년 이상',
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
        careerInfo: '경력 4년 이상',
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
        careerInfo: '박사',
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
];
