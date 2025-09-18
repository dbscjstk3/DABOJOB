import { type NewsResponse } from '@/lib/api';

export const mockNewsData: Record<string, NewsResponse[]> = {
  '1': [
    // 삼성전자 관련 뉴스
    {
      newsId: 1,
      summaryHashtagId: 10,
      newsUrl: 'https://news.example.com/samsung-hbm-production',
      newsTitle: '삼성전자, HBM3E 양산 본격화로 AI 반도체 시장 선도',
      newsContent:
        '삼성전자가 차세대 고대역폭 메모리 반도체인 HBM3E의 양산을 본격화하며 AI 반도체 시장에서의 리더십을 강화하고 있습니다. HBM3E는 기존 HBM3 대비 50% 향상된 성능을 제공하며, 엔비디아의 차세대 AI 가속기에 독점 공급될 예정입니다. 이번 양산 개시로 삼성전자는 2025년 HBM 시장에서 50% 이상의 점유율을 확보할 것으로 전망됩니다.',
      newsCreateDate: '2024-12-20',
    },
    {
      newsId: 2,
      summaryHashtagId: 11,
      newsUrl: 'https://news.example.com/samsung-ai-investment',
      newsTitle: '삼성전자, AI 반도체 개발에 3년간 100조원 투자 계획 발표',
      newsContent:
        '삼성전자가 인공지능 반도체 기술 개발과 생산 능력 확대를 위해 향후 3년간 100조원 규모의 대규모 투자를 단행한다고 발표했습니다. 이번 투자는 차세대 HBM, PIM(Processing In Memory) 기술, 그리고 AI 전용 칩셋 개발에 집중될 예정입니다. 또한 평택과 화성에 새로운 생산라인을 구축하여 글로벌 AI 반도체 공급망에서의 경쟁력을 강화할 계획입니다.',
      newsCreateDate: '2024-12-19',
    },
    {
      newsId: 3,
      summaryHashtagId: 12,
      newsUrl: 'https://news.example.com/samsung-3nm-process',
      newsTitle: '삼성전자 3나노 공정, 글로벌 파운드리 수주 급증',
      newsContent:
        '삼성전자의 3나노 GAA(Gate-All-Around) 공정 기술이 글로벌 팹리스 기업들로부터 잇따른 수주를 받으며 파운드리 사업의 성장을 견인하고 있습니다. 퀄컴, AMD, 테슬라 등 주요 고객사들이 차세대 칩 생산을 위해 삼성의 3나노 공정을 선택하고 있으며, 이는 TSMC와의 기술 격차를 좁히는 중요한 성과로 평가받고 있습니다.',
      newsCreateDate: '2024-12-18',
    },
    {
      newsId: 4,
      summaryHashtagId: 13,
      newsUrl: 'https://news.example.com/samsung-sustainability',
      newsTitle: '삼성전자, 2030년 탄소중립 목표 달성을 위한 RE100 확대',
      newsContent:
        '삼성전자가 2030년 탄소중립 목표 달성을 위해 재생에너지 사용을 대폭 확대한다고 발표했습니다. 현재 미국과 유럽 사업장에서 100% 재생에너지를 사용하고 있으며, 한국 내 주요 생산기지에도 태양광 발전소와 풍력 발전 시설을 추가로 도입할 예정입니다. 이를 통해 2030년까지 전 사업장에서 RE100을 달성하고 탄소 배출량을 2019년 대비 50% 이상 줄일 계획입니다.',
      newsCreateDate: '2024-12-17',
    },
    {
      newsId: 5,
      summaryHashtagId: 14,
      newsUrl: 'https://news.example.com/samsung-earnings-q4',
      newsTitle: '삼성전자 4분기 실적, 메모리 반도체 호황으로 사상 최대 매출 전망',
      newsContent:
        '삼성전자가 4분기에 메모리 반도체 가격 상승과 AI 수요 급증에 힘입어 사상 최대 매출을 기록할 것으로 전망됩니다. HBM과 DDR5 DRAM의 강세가 지속되고 있으며, 특히 데이터센터용 고부가가치 제품의 비중이 크게 증가했습니다. 증권가에서는 4분기 매출이 전년 동기 대비 30% 이상 증가한 80조원을 넘어설 것으로 예상한다고 분석했습니다.',
      newsCreateDate: '2024-12-16',
    },
  ],
  '2': [
    // LG전자 관련 뉴스
    {
      newsId: 6,
      summaryHashtagId: 20,
      newsUrl: 'https://news.example.com/lg-ev-components',
      newsTitle: 'LG전자, GM과 전기차 부품 공급 계약 50조원 규모로 확대',
      newsContent:
        'LG전자가 제너럴모터스(GM)와 전기차 핵심 부품 공급 계약을 기존 30조원에서 50조원 규모로 확대했다고 발표했습니다. 새로운 계약에는 차세대 전기차 플랫폼용 인버터, 온보드 충전기, 배터리 관리 시스템이 포함되며, 2030년까지 공급될 예정입니다. 이번 계약으로 LG전자는 북미 전기차 시장에서의 입지를 더욱 공고히 할 것으로 기대됩니다.',
      newsCreateDate: '2024-12-20',
    },
    {
      newsId: 7,
      summaryHashtagId: 21,
      newsUrl: 'https://news.example.com/lg-oled-innovation',
      newsTitle: 'LG전자, 차세대 마이크로OLED 기술로 AR/VR 시장 진출',
      newsContent:
        'LG전자가 초고해상도 마이크로OLED 디스플레이 기술을 상용화하며 AR/VR 시장에 본격 진출한다고 밝혔습니다. 새로운 마이크로OLED는 4K 해상도에 5000nit의 높은 밝기를 제공하며, 메타, 애플 등 글로벌 IT 기업들과 공급 협의를 진행 중입니다. 이 기술은 기존 LCD 대비 90% 작은 크기로 구현 가능해 웨어러블 기기의 소형화에 크게 기여할 것으로 전망됩니다.',
      newsCreateDate: '2024-12-19',
    },
  ],
  '3': [
    // SK하이닉스 관련 뉴스
    {
      newsId: 8,
      summaryHashtagId: 30,
      newsUrl: 'https://news.example.com/sk-hynix-hbm4',
      newsTitle: 'SK하이닉스, HBM4 개발 완료로 AI 메모리 시장 주도권 확보',
      newsContent:
        'SK하이닉스가 차세대 고대역폭 메모리인 HBM4 개발을 완료하고 2025년 하반기부터 양산에 들어간다고 발표했습니다. HBM4는 기존 HBM3E 대비 2배 향상된 성능을 제공하며, 엔비디아의 차차세대 AI 칩에 독점 공급될 예정입니다. 이로써 SK하이닉스는 AI 메모리 분야에서 글로벌 시장 점유율 1위를 더욱 공고히 할 것으로 전망됩니다.',
      newsCreateDate: '2024-12-20',
    },
    {
      newsId: 9,
      summaryHashtagId: 31,
      newsUrl: 'https://news.example.com/sk-hynix-cxl',
      newsTitle: 'SK하이닉스, CXL 메모리로 데이터센터 시장 공략 본격화',
      newsContent:
        'SK하이닉스가 차세대 컴퓨팅 인터페이스인 CXL(Compute Express Link) 기반 메모리 제품을 출시하며 데이터센터 시장 공략에 나섰습니다. CXL 메모리는 기존 메모리 대비 10배 빠른 데이터 처리 속도를 제공하며, 인텔, AMD 등 주요 서버 CPU 업체들과의 협력을 통해 차세대 서버 시스템에 적용될 예정입니다. 이를 통해 클라우드 컴퓨팅과 AI 워크로드 처리 성능이 대폭 향상될 것으로 기대됩니다.',
      newsCreateDate: '2024-12-18',
    },
  ],
};
