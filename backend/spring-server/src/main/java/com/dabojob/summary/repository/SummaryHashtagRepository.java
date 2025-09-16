package com.dabojob.summary.repository;

import com.dabojob.summary.entity.ChapterType;
import com.dabojob.summary.entity.CompanyAnalysisSummary;
import com.dabojob.summary.entity.Hashtag;
import com.dabojob.summary.entity.SummaryHashtag;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface SummaryHashtagRepository extends JpaRepository<SummaryHashtag,Long> {

    boolean existsBySummaryAndHashtag(CompanyAnalysisSummary summary, Hashtag hashtag);
    SummaryHashtag findFirstBySummary(CompanyAnalysisSummary summary);

    List<SummaryHashtag> findBySummary_SummaryId(Long summaryId);
    SummaryHashtag findBySummaryAndHashtag(CompanyAnalysisSummary summary, Hashtag hashtag);
}
