package com.dabojob.company.repository;

import com.dabojob.company.entity.DartCompany;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface DartCompanyRepository extends JpaRepository<DartCompany, Long> {
    Optional<DartCompany> findByDartId(Long dartId);
}
