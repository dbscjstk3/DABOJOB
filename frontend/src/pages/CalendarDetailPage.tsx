import { useState } from 'react';
import ReportContainer from '@/components/calendar-detail/organisms/ReportContainer';
import { Link } from '@tanstack/react-router';
import { ChevronsLeft, SquareArrowOutUpRight } from 'lucide-react';
import Typography from '@/components/common/atoms/Typography';
import { Button } from '@/components/common/atoms/Button';
import { cn } from '@/lib/utils';

interface JobInfo {
  id: string;
  status: 'recruiting' | 'ended';
  company: string;
  date: string;
  title: string;
  applicationUrl: string;
}

export default function CalendarDetailPage() {
  const [newsFilter, setNewsFilter] = useState<string | null>(null);

  // 테스트 데이터
  const mockJobData: JobInfo = {
    id: '1',
    status: 'recruiting',
    company: '삼성전자',
    date: '2024.12.31',
    title: '소프트웨어 개발자',
    applicationUrl: 'https://www.saramin.co.kr',
  };

  const mockData = {
    title: '2024년 경제 전망 보고서',
    sections: [
      {
        title: '상반기 경제 동향',
        items: [
          {
            subtitle: '1분기 실적',
            summary:
              '2024년 1분기 한국 경제는 예상보다 견고한 성장세를 보였습니다. GDP 성장률은 전년 동기 대비 2.8%를 기록하며, 정부가 당초 예상했던 2.3%를 크게 상회했습니다. 이러한 경제 성장의 주요 동력은 수출 부문의 강세에서 비롯되었는데, 특히 반도체와 IT 관련 제품의 수출이 전년 대비 15% 증가하며 전체 경제 성장을 견인했습니다. 내수 시장 역시 회복세를 보이며 소비자 신뢰지수가 3개월 연속 상승하는 모습을 나타냈습니다. 고용 상황도 개선되어 실업률이 2.9%로 하락했으며, 특히 청년층 고용률이 크게 개선되었습니다. 그러나 인플레이션 압력은 여전히 존재하여 소비자물가지수가 3.2%를 기록하며 정부와 한국은행의 지속적인 모니터링이 필요한 상황입니다.',
          },
          {
            subtitle: '2분기 전망',
            summary:
              '2분기 한국 경제는 글로벌 경제 불확실성 속에서도 상대적으로 안정적인 성장을 지속할 것으로 전망됩니다. 미중 무역갈등의 장기화와 유럽 경제의 둔화 우려에도 불구하고, 정부의 적극적인 재정정책과 한국은행의 신중한 통화정책이 경제 안정에 기여할 것으로 예상됩니다. 수출 부문에서는 중국 경제의 점진적 회복과 함께 반도체 사이클의 회복세가 본격화되면서 IT 수출이 지속적으로 증가할 것으로 보입니다. 내수 부문에서는 정부의 소상공인 지원정책과 가계소득 증대 정책의 효과가 나타나면서 민간소비가 회복될 전망입니다. 다만, 부동산 시장의 조정과 가계부채 증가율 둔화는 내수 회복의 제약 요인으로 작용할 가능성이 있어 신중한 접근이 필요합니다.',
          },
          {
            summary:
              '상반기 전체를 종합해보면, 한국 경제는 대내외 불확실성에도 불구하고 구조적 경쟁력을 바탕으로 안정적인 성장 궤도를 유지하고 있습니다. 특히 IT 산업의 글로벌 경쟁력 강화와 신재생에너지, 바이오헬스 등 신성장 동력 산업의 육성이 경제 성장의 새로운 엔진 역할을 하고 있습니다. 정부는 디지털 뉴딜과 그린 뉴딜 정책을 통해 경제 구조의 디지털 전환과 탄소중립 목표 달성을 동시에 추진하고 있으며, 이는 중장기적으로 한국 경제의 지속가능한 성장 기반을 구축하는 데 기여할 것으로 평가됩니다. 다만, 글로벌 공급망 재편과 지정학적 리스크 증가는 한국 경제가 직면한 주요 도전 과제로 남아있어 이에 대한 선제적 대응이 필요한 상황입니다.',
          },
        ],
        tags: ['경제', '상반기', '성장'],
      },
      {
        title: '하반기 시장 전망',
        items: [
          {
            subtitle: '3분기 예측',
            summary:
              '2024년 3분기는 여름휴가철 특수와 함께 서비스업 중심의 경기 회복이 예상됩니다. 관광산업과 외식업계의 매출 증가가 기대되며, 특히 해외여행 수요의 정상화로 항공업계와 관련 서비스업의 실적 개선이 전망됩니다. IT 섹터에서는 인공지능과 클라우드 서비스 수요 증가로 관련 기업들의 성장이 지속될 것으로 보입니다. 반도체 업계는 메모리 반도체 가격 회복과 시스템 반도체 수요 증가로 실적 개선이 기대됩니다. 제조업 부문에서는 자동차 산업의 전기차 전환 가속화와 배터리 기술 발전으로 관련 기업들의 투자 확대가 예상됩니다. 금융시장에서는 미국 연방준비제도의 금리 정책 변화에 따른 자금 흐름 변동이 주요 변수로 작용할 것으로 예상되며, 이에 따른 환율 변동성도 주의 깊게 모니터링해야 할 상황입니다.',
          },
          {
            subtitle: '4분기 예측',
            summary:
              '연말을 앞둔 4분기는 전통적으로 소비 증가 시즌으로 내수 경기 활성화가 기대됩니다. 추석과 연말연시 특수로 유통업계와 백화점, 온라인 쇼핑몰의 매출 급증이 예상되며, 이는 전체 소비 지표 개선으로 이어질 것으로 전망됩니다. 제조업에서는 연말 실적 마감을 위한 출하량 증가와 함께 2025년 사업계획 수립에 따른 설비투자가 활발해질 것으로 예상됩니다. 수출 부문에서는 크리스마스 시즌을 겨냥한 소비재 수출과 IT 제품의 연말 수요 증가로 실적 개선이 기대됩니다. 부동산 시장은 정부의 주택공급 확대 정책과 금리 안정화 기대감으로 거래량이 점진적으로 회복될 것으로 보입니다. 다만, 연말 유동성 증가에 따른 인플레이션 압력과 글로벌 경제 둔화 우려는 여전히 리스크 요인으로 남아있어 정책당국의 세심한 대응이 필요한 상황입니다.',
          },
        ],
        tags: ['시장', '하반기', '전망'],
      },
      {
        items: [
          {
            summary:
              '2024년 한국 경제는 대내외 복합적 도전에도 불구하고 구조적 혁신과 정책적 뒷받침을 통해 안정적 성장을 달성할 것으로 종합 평가됩니다. 연간 GDP 성장률은 2.6~2.8% 수준을 유지하며, 이는 OECD 주요국 대비 양호한 수준입니다. IT 산업의 글로벌 리더십 확보와 바이오헬스, 신재생에너지 등 미래 성장동력 육성이 경제성장의 핵심 요인으로 작용했습니다. 특히 K-반도체 벨트 구축과 차세대 배터리 기술 개발은 중장기 경쟁력 강화의 토대가 되었습니다. 고용시장도 전반적으로 안정세를 보이며 청년 고용률 개선과 여성 경제활동 참가율 증가가 두드러졌습니다. 그러나 글로벌 공급망 재편, 기후변화 대응, 인구구조 변화 등 구조적 과제에 대한 장기적 대응 전략 수립이 향후 지속가능한 성장을 위한 핵심 과제로 남아있습니다. 정부는 디지털 전환 가속화, 탄소중립 실현, 사회안전망 강화를 통해 포용적이고 지속가능한 경제성장 기반을 구축해 나갈 계획입니다.',
          },
        ],
        tags: ['분석', 'IT', '바이오'],
      },
    ],
  };

  return (
    <div className="max-w-4xl mx-auto p-4 space-y-4">
      <Link to="/" className="inline-flex items-center gap-1.5 text-sm mb-4">
        <ChevronsLeft className="h-4 w-4 text-daboja-default" />
        <span>캘린더로 돌아가기</span>
      </Link>

      {/* 채용공고 섹션 */}
      <div className="rounded-xl border border-slate-200 bg-white p-4 md:p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            {/* 상태 */}
            <Typography
              variant="default"
              weight="semibold"
              className={cn(
                'text-md',
                mockJobData.status === 'recruiting' ? 'text-daboja-default' : 'text-red-600',
              )}
            >
              {mockJobData.status === 'recruiting' ? '시작' : '마감'}
            </Typography>

            {/* 회사명 */}
            <Typography variant="default" weight="semibold">
              {mockJobData.company}
            </Typography>

            {/* 공고명 */}
            <Typography variant="subtitle" weight="bold">
              {mockJobData.title}
            </Typography>
          </div>

          {/* 버튼 */}
          <Button
            size="md"
            onClick={() => window.open(mockJobData.applicationUrl, '_blank')}
            endIcon={<SquareArrowOutUpRight className="h-4 w-4" />}
          >
            지원공고 보러가기
          </Button>
        </div>
      </div>
      <ReportContainer
        title={mockData.title}
        sections={mockData.sections}
        onTagSelect={setNewsFilter}
      />

      {/* 선택된 태그 확인용 (임시) */}
      {newsFilter && <div className="p-2 bg-blue-50 rounded">선택된 필터: #{newsFilter}</div>}
    </div>
  );
}
