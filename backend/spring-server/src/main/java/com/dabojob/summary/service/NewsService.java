package com.dabojob.summary.service;

import com.dabojob.summary.dto.NewsResponse;
import com.dabojob.summary.entity.News;
import com.dabojob.summary.repository.NewsRepository;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class NewsService {

    private final NewsRepository newsRepository;

    public List<NewsResponse> getNews(String summaryId, String hashtagName) {
        try{
            Long parsedSummaryId = Long.parseLong(summaryId);
            List<News> newsList;
            if (hashtagName == null) {
                newsList = newsRepository.findBySummaryHashtagId(parsedSummaryId);
            } else{
                newsList = newsRepository.findBySummaryHashtagIdAndHashtagName(parsedSummaryId, hashtagName);
            }

            return newsList.stream()
                    .map(NewsResponse::of)
                    .toList();
        } catch(NumberFormatException e){
            throw new IllegalArgumentException("Invalid summary ID format: " + summaryId);
        }

    }
}
