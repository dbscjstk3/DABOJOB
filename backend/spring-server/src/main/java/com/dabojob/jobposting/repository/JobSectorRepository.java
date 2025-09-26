package com.dabojob.jobposting.repository;

import com.dabojob.jobposting.entity.JobSector;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface JobSectorRepository extends JpaRepository<JobSector,Long> {
}
