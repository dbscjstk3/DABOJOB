package com.dabojob.jobposting.repository;

import com.dabojob.jobposting.entity.DartJob;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface DartJobRepository extends JpaRepository<DartJob,Long> {
}
