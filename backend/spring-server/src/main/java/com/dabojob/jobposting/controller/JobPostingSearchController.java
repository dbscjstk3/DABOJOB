package com.dabojob.jobposting.controller;

import com.dabojob.jobposting.service.SearchHistoryService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@Slf4j
@RestController
@RequestMapping("/api/job-postings/search")
@RequiredArgsConstructor
public class JobPostingSearchController {

    private final SearchHistoryService searchHistoryService;

    //사용자의 최근 검색어 조회
    @GetMapping("/recent")
    public ResponseEntity<List<String>> getRecentSearches(
            @RequestParam(defaultValue = "10") int limit,
            Authentication authentication) {
        String userId = authentication.getName();
        List<String> recentSearches = searchHistoryService.getUserRecentSearches(userId, limit);
        return ResponseEntity.ok(recentSearches);
    }

    // 전체 인기 검색어 조회
    @GetMapping("/popular")
    public ResponseEntity<List<String>> getPopularSearches(
            @RequestParam(defaultValue = "10") int limit) {
        List<String> popularSearches = searchHistoryService.getPopularSearches(limit);
        return ResponseEntity.ok(popularSearches);
    }

    // 사용자의 특정 검색어 삭제
    @DeleteMapping("/recent/{searchKeyword}")
    public ResponseEntity<Void> removeSearchHistory(
            @PathVariable String searchKeyword,
            Authentication authentication) {
        String userId = authentication.getName();
        searchHistoryService.removeUserSearchHistory(userId, searchKeyword);
        return ResponseEntity.noContent().build();
    }

    //사용자의 모든 검색어 기록 삭제
    @DeleteMapping("/recent")
    public ResponseEntity<Void> clearSearchHistory(Authentication authentication) {
        String userId = authentication.getName();
        searchHistoryService.clearUserSearchHistory(userId);
        return ResponseEntity.noContent().build();
    }
}