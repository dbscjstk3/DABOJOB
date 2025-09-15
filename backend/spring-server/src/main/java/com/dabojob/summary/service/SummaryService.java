package com.dabojob.summary.service;

import com.dabojob.summary.dto.SummaryResponse;
import com.dabojob.summary.entity.CompanyAnalysisSummary;
import com.dabojob.summary.repository.CompanyAnalysisSummaryRepository;
import jakarta.persistence.EntityNotFoundException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.stereotype.Service;

@Slf4j
@Service
@RequiredArgsConstructor
public class SummaryService {

    private final CompanyAnalysisSummaryRepository summaryRepository;

    public SummaryResponse getSummary(String summaryId) {
        try {
            Long id = Long.parseLong(summaryId);

            CompanyAnalysisSummary summary = summaryRepository.findById(id)
                    .orElseThrow(() -> new EntityNotFoundException("Summary not found with id: " + summaryId));

            return SummaryResponse.of(summary);

        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("Invalid summary ID format: " + summaryId);
        }
    }

    public Page<SummaryResponse> searchSummary(String query) {
        //TODO: 엘라스틱 서치 도입 후 서치 로직 도입
        return Page.empty();
    }
}
