package com.dabojob.jobposting.repository;

import com.dabojob.jobposting.entity.JobPosting;
import java.util.List;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

@Repository
public interface JobPostingRepository extends JpaRepository<JobPosting,Long> {

    @Query("SELECT jp FROM JobPosting jp JOIN FETCH jp.dartJob WHERE jp.jobPostingId = :jobPostingId")
    Optional<JobPosting> findByJobPostingIdWithDartJob(@Param("jobPostingId") Long jobPostingId);

    @Query("SELECT jp FROM JobPosting jp " +
            "JOIN FETCH jp.dartJob dj " +
            "WHERE dj.dartCompany.dartId = :dartCompanyId")
    Page<JobPosting> findByDartCompanyId(@Param("dartCompanyId") Long dartCompanyId, Pageable pageable);

    @Query("SELECT jp FROM JobPosting jp " +
            "JOIN FETCH jp.dartJob dj " +
            "WHERE (jp.postingTimeStamp BETWEEN :startTimestamp AND :endTimestamp) OR " +
            "(jp.expirationTimestamp BETWEEN :startTimestamp AND :endTimestamp)")
    List<JobPosting> findByDateRange(@Param("startTimestamp") Long startTimestamp,
                                     @Param("endTimestamp") Long endTimestamp);
}
