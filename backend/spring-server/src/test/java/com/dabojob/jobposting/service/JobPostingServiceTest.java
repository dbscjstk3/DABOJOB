package com.dabojob.jobposting.service;

import com.dabojob.fixture.jobposting.JobPostingFixture;
import com.dabojob.jobposting.dto.JobPostingResponse;
import com.dabojob.jobposting.entity.JobPosting;
import com.dabojob.jobposting.repository.JobPostingRepository;
import jakarta.persistence.EntityNotFoundException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;

import java.time.LocalDate;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@DisplayName("JobPostingService 테스트")
class JobPostingServiceTest {

    @Mock
    private JobPostingRepository jobPostingRepository;

    @InjectMocks
    private JobPostingService jobPostingService;

    private JobPosting jobPosting1;
    private JobPosting jobPosting2;

    @BeforeEach
    void setUp() {

        jobPosting1 = JobPostingFixture.defaultJobPosting();
        jobPosting2 = JobPostingFixture.seniorJobPosting();
    }

    @Test
    @DisplayName("getJobPosting: 정상적인 채용공고 조회")
    void getJobPosting_Success() {
        // given
        String jobPostingId = "100";

        when(jobPostingRepository.findById(100L))
                .thenReturn(Optional.of(jobPosting1));

        // when
        JobPostingResponse result = jobPostingService.getJobPosting(jobPostingId);

        // then
        assertThat(result.getJobPostingId()).isEqualTo(100L);
        assertThat(result.getCompanyId()).isEqualTo(1L);
        assertThat(result.getCompanyName()).isEqualTo("테스트 회사");
        assertThat(result.getTitle()).isEqualTo("Spring Boot 백엔드 개발자");
        assertThat(result.getUrl()).isEqualTo("https://example.com/job100");
        assertThat(result.getJobSectorId()).isEqualTo(1L);
        assertThat(result.getJobSectorName()).isEqualTo("백엔드 개발");
        assertThat(result.getJobSectorCategory()).isEqualTo("개발");
        assertThat(result.getCareerInfo()).isEqualTo("JUNIOR");
        assertThat(result.getPostingDate()).isEqualTo(LocalDate.of(2024, 1, 1));
        assertThat(result.getDeadlineDate()).isEqualTo(LocalDate.of(2024, 1, 31));

        verify(jobPostingRepository).findById(100L);
    }

    @Test
    @DisplayName("getJobPosting: 존재하지 않는 채용공고 ID")
    void getJobPosting_NotFound_ThrowsException() {
        // given
        String jobPostingId = "999";

        when(jobPostingRepository.findById(999L))
                .thenReturn(Optional.empty());

        // when & then
        assertThatThrownBy(() -> jobPostingService.getJobPosting(jobPostingId))
                .isInstanceOf(EntityNotFoundException.class)
                .hasMessage("Resource not found");  // 변경된 메시지

        verify(jobPostingRepository).findById(999L);
    }

    @Test
    @DisplayName("getJobPosting: 잘못된 ID 형식")
    void getJobPosting_InvalidFormat_ThrowsException() {
        // given
        String invalidJobPostingId = "invalid123";

        // when & then
        assertThatThrownBy(() -> jobPostingService.getJobPosting(invalidJobPostingId))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("Invalid ID format");  // 변경된 메시지

        verify(jobPostingRepository, never()).findById(anyLong());
    }

    @Test
    @DisplayName("getJobPostingByCompanyId: 정상적인 페이징 조회")
    void getJobPostingByCompanyId_Success() {
        // given
        String companyId = "1";
        int page = 0;
        int size = 10;
        Pageable pageable = PageRequest.of(page, size);

        List<JobPosting> jobPostings = Arrays.asList(jobPosting1, jobPosting2);
        Page<JobPosting> jobPostingPage = new PageImpl<>(jobPostings, pageable, jobPostings.size());

        when(jobPostingRepository.findByCompanyId(1L, pageable))
                .thenReturn(jobPostingPage);

        // when
        Page<JobPostingResponse> result = jobPostingService.getJobPostingByCompanyId(companyId, page, size);

        // then
        assertThat(result.getContent()).hasSize(2);
        assertThat(result.getTotalElements()).isEqualTo(2);
        assertThat(result.getNumber()).isEqualTo(0);
        assertThat(result.getSize()).isEqualTo(10);

        JobPostingResponse firstResponse = result.getContent().get(0);
        assertThat(firstResponse.getJobPostingId()).isEqualTo(100L);
        assertThat(firstResponse.getCompanyId()).isEqualTo(1L);
        assertThat(firstResponse.getTitle()).isEqualTo("Spring Boot 백엔드 개발자");

        verify(jobPostingRepository).findByCompanyId(1L, pageable);
    }

    @Test
    @DisplayName("getJobPostingByCompanyId: 빈 페이지 반환")
    void getJobPostingByCompanyId_EmptyPage() {
        // given
        String companyId = "1";
        int page = 0;
        int size = 10;
        Pageable pageable = PageRequest.of(page, size);

        Page<JobPosting> emptyPage = new PageImpl<>(Collections.emptyList(), pageable, 0);

        when(jobPostingRepository.findByCompanyId(1L, pageable))
                .thenReturn(emptyPage);

        // when
        Page<JobPostingResponse> result = jobPostingService.getJobPostingByCompanyId(companyId, page, size);

        // then
        assertThat(result.getContent()).isEmpty();
        assertThat(result.getTotalElements()).isZero();
        assertThat(result.getNumber()).isEqualTo(0);
        assertThat(result.getSize()).isEqualTo(10);

        verify(jobPostingRepository).findByCompanyId(1L, pageable);
    }

    @Test
    @DisplayName("getJobPostingByCompanyId: 잘못된 회사 ID 형식")
    void getJobPostingByCompanyId_InvalidFormat_ThrowsException() {
        // given
        String invalidCompanyId = "abc123";
        int page = 0;
        int size = 10;

        // when & then
        assertThatThrownBy(() -> jobPostingService.getJobPostingByCompanyId(invalidCompanyId, page, size))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("Invalid ID format");  // 변경된 메시지

        verify(jobPostingRepository, never()).findByCompanyId(anyLong(), any(Pageable.class));
    }

    @Test
    @DisplayName("getJobPostingsByDate: 정상적인 날짜 범위 조회")
    void getJobPostingsByDate_Success() {
        // given
        LocalDate startDate = LocalDate.of(2024, 1, 1);
        LocalDate endDate = LocalDate.of(2024, 1, 31);

        List<JobPosting> jobPostings = Arrays.asList(jobPosting1, jobPosting2);

        when(jobPostingRepository.findByDateRange(startDate, endDate))
                .thenReturn(jobPostings);

        // when
        List<JobPostingResponse> result = jobPostingService.getJobPostingsByDate(startDate, endDate);

        // then
        assertThat(result).hasSize(2);

        JobPostingResponse firstResponse = result.get(0);
        assertThat(firstResponse.getJobPostingId()).isEqualTo(100L);
        assertThat(firstResponse.getTitle()).isEqualTo("Spring Boot 백엔드 개발자");
        assertThat(firstResponse.getPostingDate()).isEqualTo(LocalDate.of(2024, 1, 1));

        JobPostingResponse secondResponse = result.get(1);
        assertThat(secondResponse.getJobPostingId()).isEqualTo(101L);
        assertThat(secondResponse.getTitle()).isEqualTo("React 시니어 개발자");

        verify(jobPostingRepository).findByDateRange(startDate, endDate);
    }

    @Test
    @DisplayName("getJobPostingsByDate: 빈 결과 반환")
    void getJobPostingsByDate_EmptyResult() {
        // given
        LocalDate startDate = LocalDate.of(2025, 1, 1);
        LocalDate endDate = LocalDate.of(2025, 1, 31);

        when(jobPostingRepository.findByDateRange(startDate, endDate))
                .thenReturn(Collections.emptyList());

        // when
        List<JobPostingResponse> result = jobPostingService.getJobPostingsByDate(startDate, endDate);

        // then
        assertThat(result).isEmpty();
        verify(jobPostingRepository).findByDateRange(startDate, endDate);
    }

    @Test
    @DisplayName("getJobPostingsByDate: 시작일과 종료일이 같은 경우")
    void getJobPostingsByDate_SameStartAndEndDate() {
        // given
        LocalDate sameDate = LocalDate.of(2024, 1, 1);
        List<JobPosting> jobPostings = Arrays.asList(jobPosting1);

        when(jobPostingRepository.findByDateRange(sameDate, sameDate))
                .thenReturn(jobPostings);

        // when
        List<JobPostingResponse> result = jobPostingService.getJobPostingsByDate(sameDate, sameDate);

        // then
        assertThat(result).hasSize(1);
        assertThat(result.get(0).getJobPostingId()).isEqualTo(100L);
        verify(jobPostingRepository).findByDateRange(sameDate, sameDate);
    }

    @Test
    @DisplayName("페이징 파라미터 검증: 다양한 페이지 크기")
    void getJobPostingByCompanyId_DifferentPageSizes() {
        // given
        String companyId = "1";
        List<JobPosting> jobPostings = Arrays.asList(jobPosting1);

        // 페이지 크기 1로 테스트
        Pageable smallPageable = PageRequest.of(0, 1);
        Page<JobPosting> smallPage = new PageImpl<>(jobPostings, smallPageable, 2); // 총 2개 중 1개씩

        when(jobPostingRepository.findByCompanyId(1L, smallPageable))
                .thenReturn(smallPage);

        // when
        Page<JobPostingResponse> result = jobPostingService.getJobPostingByCompanyId(companyId, 0, 1);

        // then
        assertThat(result.getContent()).hasSize(1);
        assertThat(result.getTotalElements()).isEqualTo(2);
        assertThat(result.getTotalPages()).isEqualTo(2);
        assertThat(result.hasNext()).isTrue();

        verify(jobPostingRepository).findByCompanyId(1L, smallPageable);
    }

    @Test
    @DisplayName("날짜 범위 경계값 테스트: 미래 날짜")
    void getJobPostingsByDate_FutureDates() {
        // given
        LocalDate futureStart = LocalDate.of(2030, 1, 1);
        LocalDate futureEnd = LocalDate.of(2030, 12, 31);

        when(jobPostingRepository.findByDateRange(futureStart, futureEnd))
                .thenReturn(Collections.emptyList());

        // when
        List<JobPostingResponse> result = jobPostingService.getJobPostingsByDate(futureStart, futureEnd);

        // then
        assertThat(result).isEmpty();
        verify(jobPostingRepository).findByDateRange(futureStart, futureEnd);
    }

    @Test
    @DisplayName("JobPostingResponse 변환 로직 상세 검증")
    void getJobPosting_ResponseMappingVerification() {
        // given
        String jobPostingId = "100";

        when(jobPostingRepository.findById(100L))
                .thenReturn(Optional.of(jobPosting1));

        // when
        JobPostingResponse result = jobPostingService.getJobPosting(jobPostingId);

        // then
        // 모든 필드가 올바르게 매핑되었는지 상세 검증
        assertThat(result.getJobPostingId()).isEqualTo(jobPosting1.getId());
        assertThat(result.getCompanyId()).isEqualTo(jobPosting1.getCompany().getId());
        assertThat(result.getCompanyName()).isEqualTo(jobPosting1.getCompany().getName());
        assertThat(result.getJobSectorId()).isEqualTo(jobPosting1.getJobSector().getId());
        assertThat(result.getJobSectorName()).isEqualTo(jobPosting1.getJobSector().getName());
        assertThat(result.getJobSectorCategory()).isEqualTo(jobPosting1.getJobSector().getCategory());
        assertThat(result.getCareerInfo()).isEqualTo(jobPosting1.getCareerInfo().toString());
        assertThat(result.getPostingDate()).isEqualTo(jobPosting1.getPostingDate());
        assertThat(result.getDeadlineDate()).isEqualTo(jobPosting1.getDeadlineDate());
    }

    @Test
    @DisplayName("경계 케이스: 최대 Long 값으로 조회")
    void getJobPosting_MaxLongValue() {
        // given
        String maxJobPostingId = String.valueOf(Long.MAX_VALUE);

        when(jobPostingRepository.findById(Long.MAX_VALUE))
                .thenReturn(Optional.empty());

        // when & then
        assertThatThrownBy(() -> jobPostingService.getJobPosting(maxJobPostingId))
                .isInstanceOf(EntityNotFoundException.class)
                .hasMessage("Resource not found");

        verify(jobPostingRepository).findById(Long.MAX_VALUE);
    }
}