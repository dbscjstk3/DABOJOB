package com.dabojob.jobposting.service;

import com.dabojob.config.SearchConfig;
import com.dabojob.global.exception.SearchServiceException;
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


    public Page<JobPostingResponse> autocompleteTitles(String prefix, int size) {
        try {
            log.info("Title autocomplete with prefix: '{}'", prefix);

            if (!StringUtils.hasText(prefix) || prefix.length() < 2) {
                return Page.empty();
            }

            int adjustedSize = Math.min(size <= 0 ? 10 : size, 20);
            Pageable pageable = PageRequest.of(0, adjustedSize);

            return jobPostingSearchRepository.findTitleAutocomplete(prefix, pageable)
                    .map(JobPostingDocument::toResponse);
        } catch (Exception e) {
            log.error("Autocomplete failed for prefix: '{}', size: {}", prefix, size, e); // 상세한 로그
            throw new SearchServiceException("Autocomplete operation failed", e); // 간단한 메시지
        }
    }

    public Page<JobPostingResponse> search(String searchString, int page, int size) {
        try {
            log.info("Searching with keyword: '{}', page: {}, size: {}", searchString, page, size);

            int adjustedSize = validateAndAdjustPageSize(size);
            Pageable pageable = createPageable(page, adjustedSize);

            if (StringUtils.hasText(searchString)) {
                return searchWithWeights(searchString, pageable);
            } else {
                return jobPostingSearchRepository.findAll(pageable).map(JobPostingDocument::toResponse);
            }
        } catch (Exception e) {
            log.error("Search failed for query: '{}', page: {}, size: {}", searchString, page, size, e); // 상세한 로그
            throw new SearchServiceException("Search operation failed", e); // 간단한 메시지
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