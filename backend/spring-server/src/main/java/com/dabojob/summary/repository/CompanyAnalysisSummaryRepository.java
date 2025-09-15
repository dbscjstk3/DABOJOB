package com.dabojob.summary.repository;

import com.dabojob.summary.entity.CompanyAnalysisSummary;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface CompanyAnalysisSummaryRepository extends JpaRepository<CompanyAnalysisSummary, Long> {
}
