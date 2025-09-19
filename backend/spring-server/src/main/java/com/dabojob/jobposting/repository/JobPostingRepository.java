package com.dabojob.jobposting.repository;

import com.dabojob.jobposting.entity.JobPosting;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

@Repository
public interface JobPostingRepository extends JpaRepository<JobPosting,Long> {

    @Override
    @EntityGraph(attributePaths = {"company", "jobSector"})
    Optional<JobPosting> findById(Long id);

    @EntityGraph(attributePaths = {"company", "jobSector"})
    Page<JobPosting> findByCompanyId(@Param("companyId") Long companyId, Pageable pageable);

    @Query("SELECT jp FROM JobPosting jp " +
            "WHERE (jp.postingDate <= :endDate) AND " +
            "(jp.deadlineDate >= :startDate )")
    @EntityGraph(attributePaths = {"company", "jobSector"})
    List<JobPosting> findByDateRange(@Param("startDate") LocalDate startDate,
                                     @Param("endDate") LocalDate endDate);
}
