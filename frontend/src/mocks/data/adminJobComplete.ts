import {
  type AdminJobCompleteResponse,
  type AdminJobReprocessingResponse,
  type AdminJobApproveResponse,
} from '../../lib/api';

// Admin Job Complete 목 데이터
export const mockAdminJobCompleteData: Record<string, AdminJobCompleteResponse> = {
  '123': {
    job_id: 123,
    status: 'completed',
    company_info: {
      company_name: '삼성전자',
      company_scale: '대기업',
    },
    summary_reports: {
      business_overview:
        '삼성전자는 글로벌 기술 기업으로서 반도체, 디스플레이, 모바일 기기 등을 제조하는 종합 전자회사입니다. 1969년 설립된 이래 지속적인 기술 혁신을 통해 세계 반도체 시장을 선도하고 있으며, 특히 메모리 반도체 분야에서 세계 1위의 점유율을 보유하고 있습니다.',
      products_services:
        '주요 제품으로는 DRAM, NAND 플래시 등의 메모리 반도체, 스마트폰, 태블릿, 웨어러블 기기, OLED 디스플레이, 가전제품 등이 있습니다. 또한 시스템 LSI, 파운드리 서비스를 통해 다양한 반도체 솔루션을 제공하고 있습니다.',
      revenue_orders:
        '2023년 매출은 전년 대비 14.7% 감소한 258조 9천억원을 기록했습니다. 이는 글로벌 경제 둔화와 반도체 업황 부진의 영향입니다. 주요 고객사로는 Apple, Google, Microsoft 등이 있으며, B2B 매출이 전체의 약 70%를 차지합니다.',
      contracts_rnd:
        '연구개발 투자는 매출의 약 8-9% 수준을 유지하고 있으며, 2023년 기준 약 20조원을 투자했습니다. 주요 R&D 분야는 차세대 메모리 기술, AI 반도체, 6G 통신기술, 퀀텀닷 디스플레이 등입니다.',
      others:
        '지속가능경영을 위해 2030년까지 탄소중립 달성을 목표로 하고 있으며, 다양한 사회공헌 활동을 펼치고 있습니다. 또한 글로벌 인재 양성을 위한 교육 프로그램도 운영 중입니다.',
    },
    news_data: {
      business_overview: {
        반도체: {
          hashtag_id: 101,
          news_items: [
            {
              news_id: 1001,
              title: '삼성전자, HBM3E 양산 본격화로 AI 반도체 시장 선도',
              url: 'https://news.example.com/1001',
              published_date: '2024-01-15T08:00:00',
              summary:
                '삼성전자가 차세대 고대역폭 메모리 반도체인 HBM3E의 양산을 본격화하며 AI 반도체 시장에서의 리더십을 강화하고 있습니다.',
              company_name: '삼성전자',
              status: 'completed',
            },
            {
              news_id: 1002,
              title: '삼성 3나노 공정 기술력 인정받아 대형 파운드리 수주',
              url: 'https://news.example.com/1002',
              published_date: '2024-01-12T10:30:00',
              summary:
                '삼성전자가 3나노 GAA(Gate-All-Around) 공정 기술로 글로벌 팹리스 고객사로부터 대형 파운드리 물량을 수주했습니다.',
              company_name: '삼성전자',
              status: 'completed',
            },
          ],
        },
        AI: {
          hashtag_id: 102,
          news_items: [
            {
              news_id: 1003,
              title: '삼성전자, AI 반도체 개발에 3년간 100조원 투자 계획',
              url: 'https://news.example.com/1003',
              published_date: '2024-01-10T14:20:00',
              summary:
                '삼성전자가 인공지능 반도체 기술 개발과 생산 능력 확대를 위해 향후 3년간 100조원 규모의 대규모 투자를 단행한다고 발표했습니다.',
              company_name: '삼성전자',
              status: 'completed',
            },
          ],
        },
      },
      products_services: {
        스마트폰: {
          hashtag_id: 201,
          news_items: [
            {
              news_id: 2001,
              title: '갤럭시 S24 시리즈, AI 기능 강화로 글로벌 시장 공략',
              url: 'https://news.example.com/2001',
              published_date: '2024-01-18T09:15:00',
              summary:
                '삼성전자가 새로운 갤럭시 S24 시리즈에 Galaxy AI를 도입하여 사용자 경험을 혁신하고 글로벌 프리미엄 스마트폰 시장에서의 경쟁력을 강화하고 있습니다.',
              company_name: '삼성전자',
              status: 'completed',
            },
          ],
        },
        디스플레이: {
          hashtag_id: 202,
          news_items: [
            {
              news_id: 2002,
              title: '삼성디스플레이, 차세대 QD-OLED 패널 양산 확대',
              url: 'https://news.example.com/2002',
              published_date: '2024-01-16T11:45:00',
              summary:
                '삼성디스플레이가 퀀텀닷 OLED 기술을 적용한 차세대 디스플레이 패널의 양산을 확대하여 프리미엄 TV 시장에서의 점유율 확대를 노리고 있습니다.',
              company_name: '삼성전자',
              status: 'completed',
            },
          ],
        },
      },
      revenue_orders: {
        실적: {
          hashtag_id: 301,
          news_items: [
            {
              news_id: 3001,
              title: '삼성전자 4분기 실적, 메모리 반도체 회복세로 턴어라운드',
              url: 'https://news.example.com/3001',
              published_date: '2024-01-25T16:30:00',
              summary:
                '삼성전자가 2023년 4분기 메모리 반도체 업황 회복과 함께 견조한 실적을 기록하며 본격적인 턴어라운드에 돌입했다고 발표했습니다.',
              company_name: '삼성전자',
              status: 'completed',
            },
          ],
        },
      },
      contracts_rnd: {
        연구개발: {
          hashtag_id: 401,
          news_items: [
            {
              news_id: 4001,
              title: '삼성전자, 6G 핵심기술 개발 위해 글로벌 연구기관과 협력',
              url: 'https://news.example.com/4001',
              published_date: '2024-01-20T13:10:00',
              summary:
                '삼성전자가 6G 이동통신 기술의 핵심 요소 기술 개발을 위해 MIT, 스탠포드 등 글로벌 연구기관과 공동 연구 협약을 체결했습니다.',
              company_name: '삼성전자',
              status: 'completed',
            },
          ],
        },
      },
      others: {
        지속가능경영: {
          hashtag_id: 501,
          news_items: [
            {
              news_id: 5001,
              title: '삼성전자, 2030 탄소중립 목표 달성 위한 RE100 가입',
              url: 'https://news.example.com/5001',
              published_date: '2024-01-22T10:00:00',
              summary:
                '삼성전자가 글로벌 RE100 이니셔티브에 공식 가입하며 2030년까지 사용 전력의 100%를 재생에너지로 전환하겠다고 발표했습니다.',
              company_name: '삼성전자',
              status: 'completed',
            },
          ],
        },
      },
    },
    generated_at: '2024-01-25T15:30:00',
  },
  '456': {
    job_id: 456,
    status: 'completed',
    company_info: {
      company_name: 'LG전자',
      company_scale: '대기업',
    },
    summary_reports: {
      business_overview:
        'LG전자는 가전, 전장부품, 에너지솔루션 등을 주력으로 하는 글로벌 전자회사입니다.',
      products_services:
        '주요 제품으로는 냉장고, 세탁기, 에어컨 등의 생활가전과 전기차 부품, 태양광 모듈 등이 있습니다.',
      revenue_orders: '2023년 매출 약 84조원을 기록했으며, 해외 매출 비중이 70%를 넘습니다.',
      contracts_rnd:
        '차세대 가전 기술과 전기차 부품 기술 개발에 매출의 5% 수준을 투자하고 있습니다.',
      others: '친환경 기술 개발과 사회적 가치 창출을 위한 다양한 CSR 활동을 전개하고 있습니다.',
    },
    news_data: {
      business_overview: {
        가전: {
          hashtag_id: 601,
          news_items: [
            {
              news_id: 6001,
              title: 'LG전자, AI 씽큐 플랫폼으로 스마트홈 생태계 구축',
              url: 'https://news.example.com/6001',
              published_date: '2024-01-14T09:30:00',
              summary:
                'LG전자가 AI 기술을 활용한 씽큐 플랫폼을 통해 통합 스마트홈 서비스를 제공하며 가전 시장에서의 차별화를 추진하고 있습니다.',
              company_name: 'LG전자',
              status: 'completed',
            },
          ],
        },
      },
      products_services: {
        전기차: {
          hashtag_id: 701,
          news_items: [
            {
              news_id: 7001,
              title: 'LG전자, GM과 전기차 부품 공급 계약 체결',
              url: 'https://news.example.com/7001',
              published_date: '2024-01-17T14:45:00',
              summary:
                'LG전자가 제너럴모터스(GM)와 전기차용 인포테인먼트 시스템 및 차량용 반도체 공급 계약을 체결했다고 발표했습니다.',
              company_name: 'LG전자',
              status: 'completed',
            },
          ],
        },
      },
    },
    generated_at: '2024-01-25T15:30:00',
  },
};

// 재요약 요청 응답 목 데이터
export const mockJobReprocessingResponse: AdminJobReprocessingResponse = {
  success: true,
  message: 'Job 123 has been marked for reprocessing',
  cleanup_stats: {
    job_id: 123,
    previous_status: 'completed',
    new_status: 'reprocessing',
    deleted_news_summaries: 15,
    deleted_hashtag_news: 45,
    deleted_hashtags: 12,
    deleted_summaries: 8,
    cleanup_timestamp: '2025-09-24T10:30:15.123456',
    stream_cleanup: {
      removed_messages: 3,
      acked_pending: 1,
    },
  },
  next_steps: [
    "Job status changed to 'reprocessing'",
    'Related database data has been cleaned up',
    'Redis stream messages for this job have been removed',
    'Job is ready for summary-server processing',
  ],
};

// 승인 응답 목 데이터
export const mockJobApproveResponse: AdminJobApproveResponse = {
  job_id: 123,
  status: 'finished',
  uploaded_files: {
    companies: 'reports/2024-01-01/123/companies_20240101_150000.json',
    job_postings: 'reports/2024-01-01/123/job_postings_20240101_150000.json',
    job_sectors: 'reports/2024-01-01/123/job_sectors_20240101_150000.json',
    Dart: 'reports/2024-01-01/123/Dart_20240101_150000.json',
  },
  message: 'Job approved and uploaded to S3 successfully',
};
