package com.dabojob.summary.repository;

import com.dabojob.summary.entity.Hashtag;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface HashtagRepository  extends JpaRepository<Hashtag, Long> {
    Optional<Hashtag> findByName(String hashtagName);
}
