package com.dabojob.summary.repository;

import com.dabojob.summary.entity.News;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

@Repository
public interface NewsRepository extends JpaRepository<News, Long> {

    @Query("SELECT n FROM News n WHERE n.summaryHashtag.summary.id = :summaryId")
    List<News> findBySummaryId(@Param("summaryId") Long summaryId);

    @Query("SELECT n FROM News n " +
            "WHERE n.summaryHashtag.summary.id = :summaryId " +
            "AND n.summaryHashtag.hashtag.name = :hashtagName")
    List<News> findBySummaryHashtagIdAndHashtagName(
            @Param("summaryId") Long summaryId,
            @Param("hashtagName") String hashtagName
    );
}