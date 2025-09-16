package com.dabojob.jobposting.repository;

import com.dabojob.jobposting.entity.CompanyJobPosting;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface CompanyJobPostingRepository extends JpaRepository<CompanyJobPosting,Long> {
}
