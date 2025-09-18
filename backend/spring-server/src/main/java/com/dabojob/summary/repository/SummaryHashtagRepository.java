package com.dabojob.summary.repository;

import com.dabojob.summary.entity.CompanyAnalysisSummary;
import com.dabojob.summary.entity.Hashtag;
import com.dabojob.summary.entity.SummaryHashtag;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

@Repository
public interface SummaryHashtagRepository extends JpaRepository<SummaryHashtag,Long> {

    boolean existsBySummaryAndHashtag(CompanyAnalysisSummary summary, Hashtag hashtag);

    List<SummaryHashtag> findBySummary_Id(Long summaryId);
    SummaryHashtag findBySummaryAndHashtag(CompanyAnalysisSummary summary, Hashtag hashtag);

    @Query("SELECT DISTINCT h.name " +
            "FROM SummaryHashtag sh " +
            "JOIN sh.hashtag h " +
            "JOIN sh.summary s " +
            "WHERE s.company.id = :companyId " +
            "AND s.createdAt = (" +
            "SELECT MAX(s2.createdAt) " +
            "FROM CompanyAnalysisSummary s2 " +
            "WHERE s2.company.id = :companyId" +
            ")")
    List<String> findHashtagNamesByMostRecentSummary(@Param("companyId") Long companyId);
}
