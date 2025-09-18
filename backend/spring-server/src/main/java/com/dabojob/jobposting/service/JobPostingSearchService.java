package com.dabojob.jobposting.service;

import com.dabojob.config.SearchConfig;
import com.dabojob.jobposting.dto.JobPostingResponse;
import com.dabojob.jobposting.entity.JobPostingDocument;

import com.dabojob.jobposting.repository.JobPostingSearchRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.time.LocalDate;

@Slf4j
@Service
@RequiredArgsConstructor
public class JobPostingSearchService {


    private final JobPostingSearchRepository jobPostingSearchRepository;
    private final SearchConfig searchConfig;

    public Page<JobPostingResponse> search(String searchString, int page, int size) {
        log.info("Searching with keyword: '{}', page: {}, size: {}", searchString, page, size);

        // 페이지 크기 검증 및 조정
        int adjustedSize = validateAndAdjustPageSize(size);
        Pageable pageable = createPageable(page, adjustedSize);

        if (StringUtils.hasText(searchString)) {
            // 복잡한 가중치 검색
            return searchWithWeights(searchString, pageable);
        } else {
            // 전체 조회 (최신순)
            return jobPostingSearchRepository.findAll(pageable).map(JobPostingDocument::toResponse);
        }
    }

    private Page<JobPostingResponse> searchWithWeights(String searchString, Pageable pageable) {
        LocalDate weekAgo = LocalDate.now().minusDays(7);
        LocalDate monthAgo = LocalDate.now().minusDays(30);

        return jobPostingSearchRepository.searchWithWeights(
                searchString,
                weekAgo.toString(),
                monthAgo.toString(),
                pageable
        ).map(JobPostingDocument::toResponse);
    }

    // 간단한 검색들을 위한 편의 메소드들
    public Page<JobPostingResponse> findByCompany(String companyName, int page, int size) {
        Pageable pageable = createPageable(page, validateAndAdjustPageSize(size));
        return jobPostingSearchRepository.findByCompanyNameContaining(companyName, pageable)
                .map(JobPostingDocument::toResponse);
    }

    public Page<JobPostingResponse> findByJobSector(String sectorName, int page, int size) {
        Pageable pageable = createPageable(page, validateAndAdjustPageSize(size));
        return jobPostingSearchRepository.findByJobSectorName(sectorName, pageable)
                .map(JobPostingDocument::toResponse);
    }

    public Page<JobPostingResponse> findByCareer(String careerInfo, int page, int size) {
        Pageable pageable = createPageable(page, validateAndAdjustPageSize(size));
        return jobPostingSearchRepository.findByCareerInfo(careerInfo, pageable)
                .map(JobPostingDocument::toResponse);
    }

    private int validateAndAdjustPageSize(int size) {
        // 최대 크기 제한
        if (size > searchConfig.getPagination().getMaxSize()) {
            log.warn("Requested size {} exceeds max size {}. Using max size.",
                    size, searchConfig.getPagination().getMaxSize());
            return searchConfig.getPagination().getMaxSize();
        }

        // 최소 크기 보장
        if (size <= 0) {
            log.warn("Invalid size {}. Using default size {}",
                    size, searchConfig.getPagination().getDefaultSize());
            return searchConfig.getPagination().getDefaultSize();
        }

        return size;
    }

    private Pageable createPageable(int page, int size) {
        return PageRequest.of(page, size,
                Sort.by(Sort.Direction.DESC, "_score")
                        .and(Sort.by(Sort.Direction.DESC, "posting_date"))
        );
    }
}