package com.dabojob.summary.service;

import com.dabojob.summary.dto.SummaryResponse;
import com.dabojob.summary.entity.ChapterType;
import com.dabojob.summary.entity.CompanyAnalysisSummary;
import com.dabojob.summary.entity.SummaryHashtag;
import com.dabojob.summary.repository.CompanyAnalysisSummaryRepository;
import com.dabojob.summary.repository.SummaryHashtagRepository;
import jakarta.persistence.EntityNotFoundException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.stereotype.Service;

@Slf4j
@Service
@RequiredArgsConstructor
public class SummaryService {

    private final CompanyAnalysisSummaryRepository summaryRepository;
    private final SummaryHashtagRepository  summaryHashtagRepository;

    public SummaryResponse getSummary(String summaryId) {
        try {
            Long id = Long.parseLong(summaryId);

            CompanyAnalysisSummary summary = summaryRepository.findById(id)
                    .orElseThrow(() -> new EntityNotFoundException("Summary not found with id: " + summaryId));

            List<SummaryHashtag> allSummaryHashtags = summaryHashtagRepository.findBySummary_Id(id);

            return createSummaryResponse(summary, allSummaryHashtags);

        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("Invalid summary ID format: " + summaryId);
        }
    }

    public SummaryResponse getFirstSummaryByCompanyId(String companyId) {
        try {
            Long parsedCompanyId = Long.parseLong(companyId);

            CompanyAnalysisSummary summary = summaryRepository.findFirstByCompany_IdOrderByCreatedAtDesc(parsedCompanyId)
                    .orElseThrow(() -> new EntityNotFoundException("Summary not found with companyId: " + companyId));

            List<SummaryHashtag> allSummaryHashtags = summaryHashtagRepository.findBySummary_Id(summary.getId());

            return createSummaryResponse(summary, allSummaryHashtags);

        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("Invalid company ID format: " + companyId);
        }
    }

    private SummaryResponse createSummaryResponse(CompanyAnalysisSummary summary,
                                                  List<SummaryHashtag> allSummaryHashtags) {
        Map<ChapterType, List<String>> chapterHashtags = allSummaryHashtags.stream()
                .collect(Collectors.groupingBy(
                        SummaryHashtag::getChapterType,
                        Collectors.mapping(sh -> sh.getHashtag().getName(), Collectors.toList())
                ));

        // 빈 챕터들을 위해 모든 ChapterType 초기화
        for (ChapterType chapterType : ChapterType.values()) {
            chapterHashtags.putIfAbsent(chapterType, new ArrayList<>());
        }

        return SummaryResponse.of(summary, chapterHashtags);
    }
}
