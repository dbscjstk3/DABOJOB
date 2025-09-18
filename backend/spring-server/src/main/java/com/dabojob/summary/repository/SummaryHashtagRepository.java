package com.dabojob.summary.repository;

import com.dabojob.summary.entity.CompanyAnalysisSummary;
import com.dabojob.summary.entity.Hashtag;
import com.dabojob.summary.entity.SummaryHashtag;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface SummaryHashtagRepository extends JpaRepository<SummaryHashtag,Long> {

    boolean existsBySummaryAndHashtag(CompanyAnalysisSummary summary, Hashtag hashtag);

    List<SummaryHashtag> findBySummary_Id(Long summaryId);
    SummaryHashtag findBySummaryAndHashtag(CompanyAnalysisSummary summary, Hashtag hashtag);
}
