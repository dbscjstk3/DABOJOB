package com.dabojob.summary.service;

import com.dabojob.summary.dto.NewsResponse;
import com.dabojob.summary.entity.News;
import com.dabojob.summary.repository.NewsRepository;
import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Slf4j
@Service
@RequiredArgsConstructor
public class NewsService {

    private final NewsRepository newsRepository;

    public List<NewsResponse> getNews(String summaryId, String hashtagName) {
        try{
            Long parsedSummaryId = Long.parseLong(summaryId);
            List<News> newsList;
            if (hashtagName == null) {
                newsList = newsRepository.findBySummaryId(parsedSummaryId);
            } else{
                newsList = newsRepository.findBySummaryHashtagIdAndHashtagName(parsedSummaryId, hashtagName);
            }

            return newsList.stream()
                    .map(NewsResponse::of)
                    .toList();
        } catch(NumberFormatException e){
            log.error("Invalid summary ID format: {}", summaryId, e); // 상세한 로그
            throw new IllegalArgumentException("Invalid ID format"); // 간단한 메시지
        }

    }
}
