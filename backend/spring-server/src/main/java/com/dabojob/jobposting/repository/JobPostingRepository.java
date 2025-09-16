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

    @Query("SELECT jp FROM JobPosting jp JOIN FETCH jp.companyJobPosting WHERE jp.jobPostingId = :jobPostingId")
    Optional<JobPosting> findByJobPostingId(@Param("jobPostingId") Long jobPostingId);

    @Query("SELECT jp FROM JobPosting jp " +
            "JOIN FETCH jp.companyJobPosting dj " +
            "WHERE dj.company.companyId = :companyId")
    Page<JobPosting> findByCompanyId(@Param("companyId") Long companyId, Pageable pageable);

    @Query("SELECT jp FROM JobPosting jp " +
            "JOIN FETCH jp.companyJobPosting dj " +
            "WHERE (jp.postingTimeStamp <= :endTimestamp) AND " +
            "(jp.expirationTimestamp >= :startTimestamp )")
    List<JobPosting> findByDateRange(@Param("startTimestamp") Long startTimestamp,
                                     @Param("endTimestamp") Long endTimestamp);
}
