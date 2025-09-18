package com.dabojob.jobposting.service;

import com.dabojob.jobposting.dto.JobPostingResponse;
import com.dabojob.jobposting.entity.JobPosting;
import com.dabojob.jobposting.repository.JobPostingDocumentRepository;
import com.dabojob.jobposting.repository.JobPostingRepository;
import jakarta.persistence.EntityNotFoundException;

import java.time.LocalDate;
import java.util.List;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class JobPostingService {

    private final JobPostingRepository jobPostingRepository;
    private final JobPostingDocumentRepository jobPostingDocumentRepository;

    public JobPostingResponse getJobPosting(String jobPostingId) {
        try {
            Long parsedId = Long.parseLong(jobPostingId);

            JobPosting jobPosting = jobPostingRepository.findById(parsedId)
                    .orElseThrow(() -> new EntityNotFoundException("JobPosting not found with JobPostingId: " + jobPostingId));

            return JobPostingResponse.of(jobPosting);

        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("Invalid JobPosting ID format: " + jobPostingId);
        }
    }

    public Page<JobPostingResponse> getJobPostingByCompanyId(String companyId, int page, int size) {
        try {
            Long parsedCompanyId = Long.parseLong(companyId);
            Pageable pageable = PageRequest.of(page, size);

            Page<JobPosting> jobPostingPage = jobPostingRepository.findByCompanyId(parsedCompanyId, pageable);

            return jobPostingPage.map(JobPostingResponse::of);

        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("Invalid Company ID format: " + companyId);
        }
    }

    public List<JobPostingResponse> getJobPostingsByDate(LocalDate startDate, LocalDate endDate) {
        List<JobPosting> jobPostings = jobPostingRepository.findByDateRange(startDate, endDate);

        return jobPostings.stream()
                .map(JobPostingResponse::of)
                .collect(Collectors.toList());
    }
//
//    public Page<JobPostingResponse> searchJobPosting(String searchString, int page, int size) {
//        Pageable pageable = PageRequest.of(page, size);
//        return jobPostingDocumentRepository.searchIntegrated(searchString,pageable)
//                .map(JobPostingDocument::toResponse);
//    }
}