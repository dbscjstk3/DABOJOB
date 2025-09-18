package com.dabojob.jobposting.controller;


import com.dabojob.jobposting.dto.JobPostingResponse;
import com.dabojob.jobposting.service.JobPostingSearchService;
import com.dabojob.jobposting.service.JobPostingService;
import java.time.LocalDate;
import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@Slf4j
@RestController
@RequestMapping("/api/job-posting")
@RequiredArgsConstructor
public class JobPostingController {

    private final JobPostingService jobPostingService;
    private final JobPostingSearchService  jobPostingSearchService;

    @GetMapping("/{jobPostingId}")
    public ResponseEntity<JobPostingResponse> getJobPosting(@PathVariable String jobPostingId){
        JobPostingResponse jobPostingResponse =  jobPostingService.getJobPosting(jobPostingId);
        return ResponseEntity.ok(jobPostingResponse);
    }

    @GetMapping("/calendar")
    public ResponseEntity<List<JobPostingResponse>> getCalender(@RequestParam LocalDate startDate, @RequestParam LocalDate endDate){
        List<JobPostingResponse> jobPostingResponses = jobPostingService.getJobPostingsByDate(startDate, endDate);
        return ResponseEntity.ok(jobPostingResponses);
    }

    @GetMapping("/company/{companyId}")
    public ResponseEntity<Page<JobPostingResponse>> getJobPostingByCompanyId(@PathVariable String companyId,
                                                                             @RequestParam(defaultValue = "0") int page,
                                                                             @RequestParam(defaultValue = "20") int size){
        Page<JobPostingResponse> jobPostingResponses = jobPostingService.getJobPostingByCompanyId(companyId,page,size);
        return ResponseEntity.ok(jobPostingResponses);
    }

    @GetMapping("/search")
    public ResponseEntity<Page<JobPostingResponse>> searchJobPosting(@RequestParam String searchString,
                                                                     @RequestParam(defaultValue = "0") int page,
                                                                     @RequestParam(defaultValue = "10") int size){
        Page<JobPostingResponse> jobPostingResponses = jobPostingSearchService.search(searchString, page ,size );
        return ResponseEntity.ok(jobPostingResponses);
    }


}
