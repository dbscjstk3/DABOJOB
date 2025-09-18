package com.dabojob.summary.repository;

import com.dabojob.summary.entity.News;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

@Repository
public interface NewsRepository extends JpaRepository<News, Long> {

    @Query("SELECT n FROM News n WHERE n.summaryHashtag.id = :summaryHashtagId")
    List<News> findBySummaryHashtagId(@Param("summaryHashtagId") Long summaryHashtagId);

    @Query("SELECT n FROM News n " +
            "WHERE n.summaryHashtag.id = :summaryHashtagId " +
            "AND n.summaryHashtag.hashtag.name = :hashtagName")
    List<News> findBySummaryHashtagIdAndHashtagName(
            @Param("summaryHashtagId") Long summaryHashtagId,
            @Param("hashtagName") String hashtagName
    );
}
