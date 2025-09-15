/**
 * 채용 공고 Mock 데이터
 */

export interface RecruitData {
  event_type: 'job_posted' | 'job_expired';
  job_id: string;
  csn: string;
  company_name: string;
  title: string;
  job_code: {
    code: string;
    name: string;
  };
  job_type: {
    code: string;
    name: string;
  };
  posting_date: string;
  expiration_date: string;
}

export const recruitMap: Record<number, RecruitData[]> = {
  1: [
    {
      event_type: 'job_posted',
      job_id: '27614001',
      csn: '1138600001',
      company_name: '네이버',
      title: '프론트엔드 개발자 채용',
      job_code: {
        code: '1001',
        name: '개발·프로그래밍',
      },
      job_type: {
        code: '1',
        name: '정규직',
      },
      posting_date: '2025-09-01T09:00:00+0900',
      expiration_date: '2025-09-15T23:59:59+0900',
    },
    {
      event_type: 'job_posted',
      job_id: '27614002',
      csn: '1138600002',
      company_name: '카카오',
      title: '백엔드 개발자 채용',
      job_code: {
        code: '1001',
        name: '개발·프로그래밍',
      },
      job_type: {
        code: '1',
        name: '정규직',
      },
      posting_date: '2025-09-01T10:00:00+0900',
      expiration_date: '2025-09-20T23:59:59+0900',
    },
  ],
  2: [
    {
      event_type: 'job_posted',
      job_id: '27614003',
      csn: '1138600003',
      company_name: '삼성전자',
      title: 'AI 연구원 채용',
      job_code: {
        code: '1001',
        name: '개발·프로그래밍',
      },
      job_type: {
        code: '1',
        name: '정규직',
      },
      posting_date: '2025-09-02T09:00:00+0900',
      expiration_date: '2025-09-18T23:59:59+0900',
    },
  ],
  3: [
    {
      event_type: 'job_posted',
      job_id: '27614004',
      csn: '1138600004',
      company_name: 'LG전자',
      title: 'UI/UX 디자이너 채용',
      job_code: {
        code: '2001',
        name: '디자인',
      },
      job_type: {
        code: '1',
        name: '정규직',
      },
      posting_date: '2025-09-03T09:00:00+0900',
      expiration_date: '2025-09-22T23:59:59+0900',
    },
    {
      event_type: 'job_posted',
      job_id: '27614005',
      csn: '1138600005',
      company_name: '현대자동차',
      title: '마케팅 담당자 채용',
      job_code: {
        code: '3001',
        name: '마케팅·광고',
      },
      job_type: {
        code: '1',
        name: '정규직',
      },
      posting_date: '2025-09-03T10:00:00+0900',
      expiration_date: '2025-09-25T23:59:59+0900',
    },
  ],
  4: [
    {
      event_type: 'job_posted',
      job_id: '27614006',
      csn: '1138600006',
      company_name: 'SK하이닉스',
      title: '반도체 엔지니어 채용',
      job_code: {
        code: '4001',
        name: '생산·제조',
      },
      job_type: {
        code: '1',
        name: '정규직',
      },
      posting_date: '2025-09-04T09:00:00+0900',
      expiration_date: '2025-09-28T23:59:59+0900',
    },
  ],
  5: [
    {
      event_type: 'job_posted',
      job_id: '27614007',
      csn: '1138600007',
      company_name: 'KT',
      title: '네트워크 엔지니어 채용',
      job_code: {
        code: '5001',
        name: 'IT·인터넷',
      },
      job_type: {
        code: '1',
        name: '정규직',
      },
      posting_date: '2025-09-05T09:00:00+0900',
      expiration_date: '2025-09-30T23:59:59+0900',
    },
    {
      event_type: 'job_posted',
      job_id: '27614008',
      csn: '1138600008',
      company_name: '신한은행',
      title: '금융 상품 기획자 채용',
      job_code: {
        code: '6001',
        name: '금융·보험',
      },
      job_type: {
        code: '1',
        name: '정규직',
      },
      posting_date: '2025-09-05T10:00:00+0900',
      expiration_date: '2025-09-29T23:59:59+0900',
    },
  ],
  6: [
    {
      event_type: 'job_posted',
      job_id: '27614009',
      csn: '1138600009',
      company_name: 'CJ제일제당',
      title: '식품 연구원 채용',
      job_code: {
        code: '7001',
        name: '연구·개발',
      },
      job_type: {
        code: '1',
        name: '정규직',
      },
      posting_date: '2025-09-06T09:00:00+0900',
      expiration_date: '2025-09-26T23:59:59+0900',
    },
  ],
  7: [
    {
      event_type: 'job_posted',
      job_id: '27614010',
      csn: '1138600010',
      company_name: '포스코',
      title: '철강 기술자 채용',
      job_code: {
        code: '8001',
        name: '생산·제조',
      },
      job_type: {
        code: '1',
        name: '정규직',
      },
      posting_date: '2025-09-07T09:00:00+0900',
      expiration_date: '2025-09-24T23:59:59+0900',
    },
    {
      event_type: 'job_posted',
      job_id: '27614011',
      csn: '1138600011',
      company_name: '쿠팡',
      title: '물류 시스템 개발자 채용',
      job_code: {
        code: '1001',
        name: '개발·프로그래밍',
      },
      job_type: {
        code: '1',
        name: '정규직',
      },
      posting_date: '2025-09-07T10:00:00+0900',
      expiration_date: '2025-09-27T23:59:59+0900',
    },
  ],
  8: [
    {
      event_type: 'job_posted',
      job_id: '27614012',
      csn: '1138600012',
      company_name: '토스',
      title: '프로덕트 매니저 채용',
      job_code: {
        code: '3001',
        name: '마케팅·광고',
      },
      job_type: {
        code: '1',
        name: '정규직',
      },
      posting_date: '2025-09-08T09:00:00+0900',
      expiration_date: '2025-09-23T23:59:59+0900',
    },
  ],
  9: [
    {
      event_type: 'job_posted',
      job_id: '27614013',
      csn: '1138600013',
      company_name: '라인',
      title: '데이터 사이언티스트 채용',
      job_code: {
        code: '1001',
        name: '개발·프로그래밍',
      },
      job_type: {
        code: '1',
        name: '정규직',
      },
      posting_date: '2025-09-09T09:00:00+0900',
      expiration_date: '2025-09-21T23:59:59+0900',
    },
    {
      event_type: 'job_posted',
      job_id: '27614014',
      csn: '1138600014',
      company_name: '당근마켓',
      title: 'iOS 개발자 채용',
      job_code: {
        code: '1001',
        name: '개발·프로그래밍',
      },
      job_type: {
        code: '1',
        name: '정규직',
      },
      posting_date: '2025-09-09T10:00:00+0900',
      expiration_date: '2025-09-19T23:59:59+0900',
    },
  ],
  10: [
    {
      event_type: 'job_posted',
      job_id: '27614015',
      csn: '1138600015',
      company_name: '우아한형제들',
      title: '안드로이드 개발자 채용',
      job_code: {
        code: '1001',
        name: '개발·프로그래밍',
      },
      job_type: {
        code: '1',
        name: '정규직',
      },
      posting_date: '2025-09-10T09:00:00+0900',
      expiration_date: '2025-09-17T23:59:59+0900',
    },
  ],
  11: [
    {
      event_type: 'job_posted',
      job_id: '27614016',
      csn: '1138600016',
      company_name: '야놀자',
      title: 'UX 디자이너 채용',
      job_code: {
        code: '2001',
        name: '디자인',
      },
      job_type: {
        code: '1',
        name: '정규직',
      },
      posting_date: '2025-09-11T09:00:00+0900',
      expiration_date: '2025-09-16T23:59:59+0900',
    },
    {
      event_type: 'job_posted',
      job_id: '27614017',
      csn: '1138600017',
      company_name: '직방',
      title: '데이터 엔지니어 채용',
      job_code: {
        code: '1001',
        name: '개발·프로그래밍',
      },
      job_type: {
        code: '1',
        name: '정규직',
      },
      posting_date: '2025-09-11T10:00:00+0900',
      expiration_date: '2025-09-14T23:59:59+0900',
    },
  ],
  12: [
    {
      event_type: 'job_posted',
      job_id: '27614018',
      csn: '1138600018',
      company_name: '마켓컬리',
      title: 'DevOps 엔지니어 채용',
      job_code: {
        code: '1001',
        name: '개발·프로그래밍',
      },
      job_type: {
        code: '1',
        name: '정규직',
      },
      posting_date: '2025-09-12T09:00:00+0900',
      expiration_date: '2025-09-19T23:59:59+0900',
    },
  ],
  13: [
    {
      event_type: 'job_posted',
      job_id: '27614019',
      csn: '1138600019',
      company_name: '뱅크샐러드',
      title: '금융 상품 기획자 채용',
      job_code: {
        code: '6001',
        name: '금융·보험',
      },
      job_type: {
        code: '1',
        name: '정규직',
      },
      posting_date: '2025-09-13T09:00:00+0900',
      expiration_date: '2025-09-21T23:59:59+0900',
    },
    {
      event_type: 'job_posted',
      job_id: '27614020',
      csn: '1138600020',
      company_name: '스포카',
      title: '프론트엔드 개발자 채용',
      job_code: {
        code: '1001',
        name: '개발·프로그래밍',
      },
      job_type: {
        code: '1',
        name: '정규직',
      },
      posting_date: '2025-09-13T10:00:00+0900',
      expiration_date: '2025-09-30T23:59:59+0900',
    },
  ],
  14: [
    {
      event_type: 'job_posted',
      job_id: '27614021',
      csn: '1138600021',
      company_name: '그린카',
      title: '백엔드 개발자 채용',
      job_code: {
        code: '1001',
        name: '개발·프로그래밍',
      },
      job_type: {
        code: '1',
        name: '정규직',
      },
      posting_date: '2025-09-14T09:00:00+0900',
      expiration_date: '2025-09-27T23:59:59+0900',
    },
  ],
  15: [
    {
      event_type: 'job_posted',
      job_id: '27614114',
      csn: '1138600917',
      company_name: '(주)사람인',
      title: '(주)사람인 사무보조·문서작성 경력 채용합니다',
      job_code: {
        code: '2323',
        name: '요리·제빵사·영양사',
      },
      job_type: {
        code: '1',
        name: '정규직',
      },
      posting_date: '2025-09-15T09:25:21+0900',
      expiration_date: '2025-09-29T23:59:59+0900',
    },
    {
      event_type: 'job_posted',
      job_id: '27614112',
      csn: '1138600917',
      company_name: '(주)사람인테스트계정04',
      title: '건축·인테리어·설계 외 2개 부문 담당자 모집 공고',
      job_code: {
        code: '건축직종코드',
        name: '건축·인테리어·설계',
      },
      job_type: {
        code: '1',
        name: '정규직',
      },
      posting_date: '2025-09-15T13:46:04+0900',
      expiration_date: '2025-09-29T23:59:59+0900',
    },
    {
      event_type: 'job_posted',
      job_id: '27614115',
      csn: '1138600918',
      company_name: '네이버',
      title: '프론트엔드 개발자 채용',
      job_code: {
        code: '1009',
        name: '개발·프로그래밍',
      },
      job_type: {
        code: '1',
        name: '정규직',
      },
      posting_date: '2025-09-15T10:00:00+0900',
      expiration_date: '2025-09-30T23:59:59+0900',
    },
    {
      event_type: 'job_posted',
      job_id: '27614116',
      csn: '1138600919',
      company_name: '카카오',
      title: '백엔드 개발자 채용',
      job_code: {
        code: '1002',
        name: '개발·프로그래밍',
      },
      job_type: {
        code: '1',
        name: '정규직',
      },
      posting_date: '2025-09-15T11:00:00+0900',
      expiration_date: '2025-09-31T23:59:59+0900',
    },
    {
      event_type: 'job_expired',
      job_id: '1344189',
      csn: '1138600928',
      company_name: '싸피',
      title: '싸피 15기 모집',
      job_code: {
        code: '1357',
        name: '싸피',
      },
      job_type: {
        code: '3',
        name: '교육생',
      },
      posting_date: '2025-08-15T19:00:00+0900',
      expiration_date: '2025-09-15T23:59:59+0900',
    },
  ],
};

/**
 * 특정 날짜의 채용 공고 데이터를 가져오는 함수
 */
export const getRecruitsByDate = (day: number): RecruitData[] => {
  return recruitMap[day] || [];
};

/**
 * 모든 채용 공고 데이터를 가져오는 함수
 */
export const getAllRecruits = (): RecruitData[] => {
  return Object.values(recruitMap).flat();
};

/**
 * 특정 회사의 채용 공고를 가져오는 함수
 */
export const getRecruitsByCompany = (companyName: string): RecruitData[] => {
  return getAllRecruits().filter((recruit) => recruit.company_name === companyName);
};

/**
 * 특정 직무 분야의 채용 공고를 가져오는 함수
 */
export const getRecruitsByJobCode = (jobCodeName: string): RecruitData[] => {
  return getAllRecruits().filter((recruit) => recruit.job_code.name === jobCodeName);
};
