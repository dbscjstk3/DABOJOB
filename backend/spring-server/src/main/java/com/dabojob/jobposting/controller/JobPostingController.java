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
@RequestMapping("/api/job-postings")
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

    @GetMapping
    public ResponseEntity<Page<JobPostingResponse>> getJobPostings(
            @RequestParam(required = false) String companyId,
            @RequestParam(required = false) String search,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size
    ) {
        if (search != null) {
            // 검색어가 있으면 ES 사용
            return ResponseEntity.ok(
                    jobPostingSearchService.search(search, page, size)
            );
        } else if (companyId != null) {
            return ResponseEntity.ok(
                    jobPostingService.getJobPostingByCompanyId(companyId, page, size)
            );
        } else{
            return ResponseEntity.ok(
                    jobPostingService.getJobPostings(page,size)
            );
        }
    }


    @GetMapping("/suggestions")
    public ResponseEntity<Page<JobPostingResponse>> autocompleteTitles(@RequestParam String prefix,
                                                                       @RequestParam(defaultValue = "10") int size) {
        Page<JobPostingResponse> suggestions = jobPostingSearchService.autocompleteTitles(prefix, size);
        return ResponseEntity.ok(suggestions);
    }


}
