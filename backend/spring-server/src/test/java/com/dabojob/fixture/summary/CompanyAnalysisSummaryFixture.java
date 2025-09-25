package com.dabojob.fixture.summary;

import com.dabojob.fixture.company.CompanyFixture;
import com.dabojob.summary.entity.CompanyAnalysisSummary;
import com.dabojob.summary.entity.SummaryStatus;
import java.util.Arrays;
import java.util.List;

public class CompanyAnalysisSummaryFixture {

    public static CompanyAnalysisSummary defaultSummary() {
        return CompanyAnalysisSummary.builder()
                .id(1L)
                .company(CompanyFixture.defaultCompany())
                .businessOverview("테스트 회사는 IT 서비스를 제공하는 중견기업입니다.")
                .productsService("웹 개발, 모바일 앱 개발, 클라우드 서비스를 제공합니다.")
                .salesContracts("주요 고객사는 금융, 제조업 분야입니다.")
                .rndActivities("AI, 빅데이터 분야에 지속적으로 투자하고 있습니다.")
                .otherNotes("직원 복지가 우수하며 업무 환경이 좋습니다.")
                .status(SummaryStatus.FINISHED)
                .build();
    }

    public static CompanyAnalysisSummary createdSummary() {
        return CompanyAnalysisSummary.builder()
                .id(2L)
                .company(CompanyFixture.largeCompany())
                .businessOverview("대기업 테스트는 글로벌 IT 서비스 기업입니다.")
                .productsService("엔터프라이즈 소프트웨어, 클라우드 인프라를 제공합니다.")
                .salesContracts("국내외 대기업을 대상으로 B2B 서비스를 제공합니다.")
                .rndActivities("블록체인, IoT 기술 개발에 집중하고 있습니다.")
                .otherNotes("글로벌 진출을 위한 투자를 확대하고 있습니다.")
                .status(SummaryStatus.CREATED)
                .build();
    }

    public static CompanyAnalysisSummary updatedSummary() {
        return CompanyAnalysisSummary.builder()
                .id(3L)
                .company(CompanyFixture.startupCompany())
                .businessOverview("스타트업 테스트는 혁신적인 핀테크 서비스를 제공합니다.")
                .productsService("모바일 결제, 개인 자산관리 앱을 개발합니다.")
                .salesContracts("B2C 고객을 대상으로 한 구독 서비스 모델입니다.")
                .rndActivities("머신러닝 기반 금융 서비스 개발에 주력합니다.")
                .otherNotes("빠른 성장세를 보이며 시리즈 B 투자를 진행 중입니다.")
                .status(SummaryStatus.UPDATED)
                .build();
    }

    public static CompanyAnalysisSummary samsungSummary() {
        return CompanyAnalysisSummary.builder()
                .id(4L)
                .company(CompanyFixture.samsungCompany())
                .businessOverview("삼성전자는 글로벌 전자제품 제조업체입니다.")
                .productsService("스마트폰, 반도체, 디스플레이, 가전제품을 제조합니다.")
                .salesContracts("전 세계 B2B, B2C 시장에서 선도적 지위를 유지합니다.")
                .rndActivities("5G, 6G 통신기술과 차세대 반도체 기술 개발에 투자합니다.")
                .otherNotes("지속가능경영과 ESG 경영에 중점을 두고 있습니다.")
                .status(SummaryStatus.FINISHED)
                .build();
    }

    public static CompanyAnalysisSummary naverSummary() {
        return CompanyAnalysisSummary.builder()
                .id(5L)
                .company(CompanyFixture.naverCompany())
                .businessOverview("네이버는 국내 최대 인터넷 포털 서비스 기업입니다.")
                .productsService("검색엔진, 클라우드 서비스, 웹툰, 쇼핑 플랫폼을 운영합니다.")
                .salesContracts("광고 수익과 커머스 수수료가 주요 매출원입니다.")
                .rndActivities("AI, 자율주행, 로보틱스 분야에 대규모 투자를 진행합니다.")
                .otherNotes("글로벌 시장 진출을 위해 해외 투자를 확대하고 있습니다.")
                .status(SummaryStatus.FINISHED)
                .build();
    }

    public static List<CompanyAnalysisSummary> defaultSummaryList() {
        return Arrays.asList(
                defaultSummary(),
                createdSummary(),
                updatedSummary()
        );
    }

    public static List<CompanyAnalysisSummary> finishedSummaryList() {
        return Arrays.asList(
                defaultSummary(),
                samsungSummary(),
                naverSummary()
        );
    }

    public static List<CompanyAnalysisSummary> inProgressSummaryList() {
        return Arrays.asList(
                createdSummary(),
                updatedSummary(),
                CompanyAnalysisSummary.builder()
                        .id(6L)
                        .company(CompanyFixture.defaultCompany())
                        .businessOverview("진행 중인 분석 리포트입니다.")
                        .status(SummaryStatus.CREATED)
                        .build()
        );
    }
}