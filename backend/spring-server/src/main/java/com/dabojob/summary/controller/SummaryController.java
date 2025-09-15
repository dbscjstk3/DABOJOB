package com.dabojob.summary.controller;

import com.dabojob.summary.dto.NewsResponse;
import com.dabojob.summary.dto.SummaryResponse;
import com.dabojob.summary.service.NewsService;
import com.dabojob.summary.service.SummaryService;
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
@RequestMapping("/api/summary")
@RequiredArgsConstructor
public class SummaryController {

    private final SummaryService summaryService;
    private final NewsService newsService;


    @GetMapping("/{summaryId}")
    public ResponseEntity<SummaryResponse> getSummary(@PathVariable String summaryId){
        SummaryResponse summaryResponse = summaryService.getSummary(summaryId);
        return ResponseEntity.ok(summaryResponse);
    }

    @GetMapping("/search")
    public ResponseEntity<Page<SummaryResponse>> searchSummary(@RequestParam String query){
        Page<SummaryResponse> summaryDTOs = summaryService.searchSummary(query);
        return ResponseEntity.ok(summaryDTOs);
    }

    @GetMapping("/{summaryId}/news")
    public ResponseEntity<List<NewsResponse>> getNews(@PathVariable String summaryId){
        List<NewsResponse> newsResponses = newsService.getNews(summaryId, null);
        return ResponseEntity.ok(newsResponses);
    }

    @GetMapping("/{summaryId}/news/{hashtagName}")
    public ResponseEntity<List<NewsResponse>> getNewsByHashtag(@PathVariable String summaryId,
                                                               @PathVariable String hashtagName){
        List<NewsResponse> newsResponses = newsService.getNews(summaryId, hashtagName);
        return ResponseEntity.ok(newsResponses);
    }


}
