package com.dabojob.summary.service;

import com.dabojob.company.entity.Company;
import com.dabojob.summary.dto.SummaryResponse;
import com.dabojob.summary.entity.*;
import com.dabojob.summary.repository.CompanyAnalysisSummaryRepository;
import com.dabojob.summary.repository.SummaryHashtagRepository;
import jakarta.persistence.EntityNotFoundException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.*;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@DisplayName("SummaryService 테스트")
class SummaryServiceTest {

    @Mock
    private CompanyAnalysisSummaryRepository summaryRepository;

    @Mock
    private SummaryHashtagRepository summaryHashtagRepository;

    @InjectMocks
    private SummaryService summaryService;

    private Company company;
    private CompanyAnalysisSummary summary;
    private List<SummaryHashtag> summaryHashtags;
    private Hashtag hashtag1, hashtag2, hashtag3;

    @BeforeEach
    void setUp() {
        // Company 설정 (CompanyScale은 테스트에서 사용하지 않으므로 임의 값 또는 null)
        company = Company.builder()
                .id(1L)
                .name("테스트 회사")
                .scale(null) // 또는 CompanyScale의 특정 값
                .build();

        // CompanyAnalysisSummary 설정
        summary = CompanyAnalysisSummary.builder()
                .id(100L)
                .company(company)
                .businessOverview("사업 개요 내용")
                .productsService("제품 서비스 내용")
                .salesContracts("영업 계약 내용")
                .rndActivities("연구개발 활동 내용")
                .otherNotes("기타 사항 내용")
                .status(SummaryStatus.FINISHED)
                .build();

        // Hashtag 설정
        hashtag1 = Hashtag.builder()
                .id(1L)
                .name("AI기술")
                .build();

        hashtag2 = Hashtag.builder()
                .id(2L)
                .name("클라우드")
                .build();

        hashtag3 = Hashtag.builder()
                .id(3L)
                .name("빅데이터")
                .build();

        // SummaryHashtag 설정 (다양한 ChapterType에 분산)
        SummaryHashtag summaryHashtag1 = SummaryHashtag.builder()
                .id(1L)
                .summary(summary)
                .hashtag(hashtag1)
                .chapterType(ChapterType.BUSINESS_OVERVIEW)
                .build();

        SummaryHashtag summaryHashtag2 = SummaryHashtag.builder()
                .id(2L)
                .summary(summary)
                .hashtag(hashtag2)
                .chapterType(ChapterType.PRODUCTS_SERVICE)
                .build();

        SummaryHashtag summaryHashtag3 = SummaryHashtag.builder()
                .id(3L)
                .summary(summary)
                .hashtag(hashtag3)
                .chapterType(ChapterType.BUSINESS_OVERVIEW)
                .build();

        summaryHashtags = Arrays.asList(summaryHashtag1, summaryHashtag2, summaryHashtag3);
    }

    @Test
    @DisplayName("정상 케이스: 챕터별로 해시태그가 올바르게 그룹핑됨")
    void getSummary_Success_WithHashtagGrouping() {
        // given
        String summaryId = "100";

        when(summaryRepository.findById(100L))
                .thenReturn(Optional.of(summary));
        when(summaryHashtagRepository.findBySummary_Id(100L))
                .thenReturn(summaryHashtags);

        // when
        SummaryResponse result = summaryService.getSummary(summaryId);

        // then
        assertThat(result.getSummaryId()).isEqualTo(100L);
        assertThat(result.getCompanyId()).isEqualTo(1L);
        assertThat(result.getCompanyName()).isEqualTo("테스트 회사");
        assertThat(result.getBusinessOverview()).isEqualTo("사업 개요 내용");

        // 챕터별 해시태그 그룹핑 검증
        Map<ChapterType, List<String>> chapterHashtags = result.getChapterHashtags();

        // BUSINESS_OVERVIEW: AI기술, 빅데이터 (2개)
        assertThat(chapterHashtags.get(ChapterType.BUSINESS_OVERVIEW))
                .hasSize(2)
                .containsExactlyInAnyOrder("AI기술", "빅데이터");

        // PRODUCTS_SERVICE: 클라우드 (1개)
        assertThat(chapterHashtags.get(ChapterType.PRODUCTS_SERVICE))
                .hasSize(1)
                .contains("클라우드");

        // 나머지 챕터들은 빈 리스트
        assertThat(chapterHashtags.get(ChapterType.SALES_CONTRACTS)).isEmpty();
        assertThat(chapterHashtags.get(ChapterType.RND_ACTIVITIES)).isEmpty();
        assertThat(chapterHashtags.get(ChapterType.OTHER_NOTES)).isEmpty();

        verify(summaryRepository).findById(100L);
        verify(summaryHashtagRepository).findBySummary_Id(100L);
    }

    @Test
    @DisplayName("정상 케이스: 해시태그가 없는 경우 모든 챕터가 빈 리스트")
    void getSummary_Success_WithEmptyHashtags() {
        // given
        String summaryId = "100";

        when(summaryRepository.findById(100L))
                .thenReturn(Optional.of(summary));
        when(summaryHashtagRepository.findBySummary_Id(100L))
                .thenReturn(Collections.emptyList());

        // when
        SummaryResponse result = summaryService.getSummary(summaryId);

        // then
        Map<ChapterType, List<String>> chapterHashtags = result.getChapterHashtags();

        // 모든 ChapterType이 존재하고 빈 리스트인지 확인
        assertThat(chapterHashtags).hasSize(ChapterType.values().length);
        for (ChapterType chapterType : ChapterType.values()) {
            assertThat(chapterHashtags.get(chapterType)).isEmpty();
        }
    }

    @Test
    @DisplayName("예외 케이스: 존재하지 않는 Summary ID")
    void getSummary_SummaryNotFound_ThrowsException() {
        // given
        String summaryId = "999";

        when(summaryRepository.findById(999L))
                .thenReturn(Optional.empty());

        // when & then
        assertThatThrownBy(() -> summaryService.getSummary(summaryId))
                .isInstanceOf(EntityNotFoundException.class)
                .hasMessage("Summary not found with id: 999");

        verify(summaryRepository).findById(999L);
        verify(summaryHashtagRepository, never()).findBySummary_Id(anyLong());
    }

    @Test
    @DisplayName("예외 케이스: 잘못된 Summary ID 형식")
    void getSummary_InvalidFormat_ThrowsException() {
        // given
        String invalidSummaryId = "invalid123";

        // when & then
        assertThatThrownBy(() -> summaryService.getSummary(invalidSummaryId))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("Invalid summary ID format: invalid123");

        verify(summaryRepository, never()).findById(anyLong());
        verify(summaryHashtagRepository, never()).findBySummary_Id(anyLong());
    }

    @Test
    @DisplayName("getFirstSummaryByCompanyId: 정상 케이스")
    void getFirstSummaryByCompanyId_Success() {
        // given
        String companyId = "1";

        when(summaryRepository.findFirstByCompany_IdOrderByCreatedAtDesc(1L))
                .thenReturn(Optional.of(summary));
        when(summaryHashtagRepository.findBySummary_Id(100L))
                .thenReturn(summaryHashtags);

        // when
        SummaryResponse result = summaryService.getFirstSummaryByCompanyId(companyId);

        // then
        assertThat(result.getSummaryId()).isEqualTo(100L);
        assertThat(result.getCompanyId()).isEqualTo(1L);
        assertThat(result.getCompanyName()).isEqualTo("테스트 회사");

        // 챕터별 해시태그가 올바르게 처리되었는지 확인
        Map<ChapterType, List<String>> chapterHashtags = result.getChapterHashtags();
        assertThat(chapterHashtags).hasSize(ChapterType.values().length);
        assertThat(chapterHashtags.get(ChapterType.BUSINESS_OVERVIEW)).hasSize(2);

        verify(summaryRepository).findFirstByCompany_IdOrderByCreatedAtDesc(1L);
        verify(summaryHashtagRepository).findBySummary_Id(100L);
    }

    @Test
    @DisplayName("getFirstSummaryByCompanyId: 존재하지 않는 Company ID")
    void getFirstSummaryByCompanyId_CompanyNotFound_ThrowsException() {
        // given
        String companyId = "999";

        when(summaryRepository.findFirstByCompany_IdOrderByCreatedAtDesc(999L))
                .thenReturn(Optional.empty());

        // when & then
        assertThatThrownBy(() -> summaryService.getFirstSummaryByCompanyId(companyId))
                .isInstanceOf(EntityNotFoundException.class)
                .hasMessage("Summary not found with companyId: 999");

        verify(summaryRepository).findFirstByCompany_IdOrderByCreatedAtDesc(999L);
        verify(summaryHashtagRepository, never()).findBySummary_Id(anyLong());
    }

    @Test
    @DisplayName("getFirstSummaryByCompanyId: 잘못된 Company ID 형식")
    void getFirstSummaryByCompanyId_InvalidFormat_ThrowsException() {
        // given
        String invalidCompanyId = "abc123";

        // when & then
        assertThatThrownBy(() -> summaryService.getFirstSummaryByCompanyId(invalidCompanyId))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("Invalid company ID format: abc123");

        verify(summaryRepository, never()).findFirstByCompany_IdOrderByCreatedAtDesc(anyLong());
        verify(summaryHashtagRepository, never()).findBySummary_Id(anyLong());
    }

    @Test
    @DisplayName("챕터별 해시태그 그룹핑 로직 상세 검증")
    void getSummary_ChapterGroupingLogic_DetailedVerification() {
        // given
        String summaryId = "100";

        // 같은 챕터에 여러 해시태그가 있는 경우
        SummaryHashtag additionalHashtag = SummaryHashtag.builder()
                .id(4L)
                .summary(summary)
                .hashtag(Hashtag.builder().id(4L).name("머신러닝").build())
                .chapterType(ChapterType.BUSINESS_OVERVIEW)
                .build();

        List<SummaryHashtag> extendedHashtags = new ArrayList<>(summaryHashtags);
        extendedHashtags.add(additionalHashtag);

        when(summaryRepository.findById(100L))
                .thenReturn(Optional.of(summary));
        when(summaryHashtagRepository.findBySummary_Id(100L))
                .thenReturn(extendedHashtags);

        // when
        SummaryResponse result = summaryService.getSummary(summaryId);

        // then
        Map<ChapterType, List<String>> chapterHashtags = result.getChapterHashtags();

        // BUSINESS_OVERVIEW에 3개의 해시태그가 있어야 함
        assertThat(chapterHashtags.get(ChapterType.BUSINESS_OVERVIEW))
                .hasSize(3)
                .containsExactlyInAnyOrder("AI기술", "빅데이터", "머신러닝");
    }

    @Test
    @DisplayName("searchSummary: 현재는 빈 페이지 반환 (TODO 상태)")
    void searchSummary_ReturnEmptyPage() {
        // given
        String query = "테스트 쿼리";

        // when
        var result = summaryService.searchSummary(query);

        // then
        assertThat(result.isEmpty()).isTrue();
        assertThat(result.getTotalElements()).isZero();
    }

    @Test
    @DisplayName("경계 케이스: summaryId가 Long.MAX_VALUE")
    void getSummary_MaxLongValue_Success() {
        // given
        String maxSummaryId = String.valueOf(Long.MAX_VALUE);

        when(summaryRepository.findById(Long.MAX_VALUE))
                .thenReturn(Optional.of(summary));
        when(summaryHashtagRepository.findBySummary_Id(Long.MAX_VALUE))
                .thenReturn(Collections.emptyList());

        // when
        SummaryResponse result = summaryService.getSummary(maxSummaryId);

        // then
        assertThat(result.getSummaryId()).isEqualTo(100L); // summary.getId()
        verify(summaryRepository).findById(Long.MAX_VALUE);
    }
}