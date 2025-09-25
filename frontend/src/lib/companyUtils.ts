import type { AdminCompany } from './api';

// 회사명에서 그룹명을 추출하는 함수
export const extractCompanyGroup = (companyName: string): string => {
  // 괄호와 주식회사 등을 제거
  const cleanName = companyName
    .replace(/\(주\)/g, '')
    .replace(/\(/g, '')
    .replace(/\)/g, '')
    .replace(/주식회사/g, '')
    .trim();

  // 주요 그룹사 패턴 매칭
  const groupPatterns = [
    { pattern: /^삼성/, group: '삼성' },
    { pattern: /^LG/, group: 'LG' },
    { pattern: /^SK/, group: 'SK' },
    { pattern: /^현대/, group: '현대' },
    { pattern: /^기아/, group: '기아' },
    { pattern: /^포스코/, group: '포스코' },
    { pattern: /^네이버/, group: '네이버' },
    { pattern: /^카카오/, group: '카카오' },
    { pattern: /^쿠팡/, group: '쿠팡' },
    { pattern: /^배달의민족/, group: '배달의민족' },
    { pattern: /^토스/, group: '토스' },
    { pattern: /^당근/, group: '당근' },
    { pattern: /^라인/, group: '라인' },
    { pattern: /^야놀자/, group: '야놀자' },
    { pattern: /^마켓컬리/, group: '마켓컬리' },
    { pattern: /^우아한형제들/, group: '우아한형제들' },
    { pattern: /^뱅크샐러드/, group: '뱅크샐러드' },
    { pattern: /^직방/, group: '직방' },
    { pattern: /^스포카/, group: '스포카' },
    { pattern: /^그린카/, group: '그린카' },
    { pattern: /^티몬/, group: '티몬' },
    { pattern: /^위메프/, group: '위메프' },
    { pattern: /^11번가/, group: '11번가' },
    { pattern: /^G마켓/, group: 'G마켓' },
    { pattern: /^옥션/, group: '옥션' },
    { pattern: /^인터파크/, group: '인터파크' },
    { pattern: /^롯데/, group: '롯데' },
    { pattern: /^신세계/, group: '신세계' },
    { pattern: /^현대백화점/, group: '현대백화점' },
    { pattern: /^하이마트/, group: '하이마트' },
    { pattern: /^이마트/, group: '이마트' },
    { pattern: /^롯데마트/, group: '롯데마트' },
    { pattern: /^홈플러스/, group: '홈플러스' },
    { pattern: /^코스트코/, group: '코스트코' },
    { pattern: /^메가마트/, group: '메가마트' },
    { pattern: /^이마트24/, group: '이마트24' },
    { pattern: /^GS25/, group: 'GS25' },
    { pattern: /^CU/, group: 'CU' },
    { pattern: /^세븐일레븐/, group: '세븐일레븐' },
    { pattern: /^미니스톱/, group: '미니스톱' },
    { pattern: /^이디야/, group: '이디야' },
    { pattern: /^스타벅스/, group: '스타벅스' },
    { pattern: /^투썸플레이스/, group: '투썸플레이스' },
    { pattern: /^커피빈/, group: '커피빈' },
    { pattern: /^엔젤리너스/, group: '엔젤리너스' },
    { pattern: /^탐앤탐스/, group: '탐앤탐스' },
    { pattern: /^카페베네/, group: '카페베네' },
    { pattern: /^빽다방/, group: '빽다방' },
    { pattern: /^메가커피/, group: '메가커피' },
  ];

  for (const { pattern, group } of groupPatterns) {
    if (pattern.test(cleanName)) {
      return group;
    }
  }

  // 패턴에 매칭되지 않으면 원본 회사명 반환
  return cleanName;
};

// 회사들을 그룹별로 분류하는 함수
export const groupCompaniesByGroup = (
  companies: AdminCompany[],
): Record<string, AdminCompany[]> => {
  const grouped: Record<string, AdminCompany[]> = {};

  companies.forEach((company) => {
    const group = extractCompanyGroup(company.company_name);
    if (!grouped[group]) {
      grouped[group] = [];
    }
    grouped[group].push(company);
  });

  return grouped;
};

// 그룹별 통계를 계산하는 함수
export const calculateGroupStats = (companies: AdminCompany[]) => {
  const grouped = groupCompaniesByGroup(companies);
  const stats: Record<string, { total: number; verified: number; failed: number }> = {};

  Object.entries(grouped).forEach(([group, groupCompanies]) => {
    stats[group] = {
      total: groupCompanies.length,
      verified: groupCompanies.filter((c) => c.mapping_status === 'verified').length,
      failed: groupCompanies.filter((c) => c.mapping_status === 'failed').length,
    };
  });

  return stats;
};
