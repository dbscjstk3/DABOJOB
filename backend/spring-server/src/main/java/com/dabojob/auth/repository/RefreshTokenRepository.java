package com.dabojob.auth.repository;

import com.dabojob.auth.repository.entity.RefreshToken;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

@Repository
public interface RefreshTokenRepository extends JpaRepository<RefreshToken, Long> {

    /**
     * 토큰 문자열로 RefreshToken 조회
     * 토큰 갱신 요청 시 사용
     */
    Optional<RefreshToken> findByUserRefreshToken(String refreshToken);

    /**
     * 사용자 ID로 모든 RefreshToken 조회
     * 사용자별 활성 토큰 관리용
     */
    List<RefreshToken> findByUserId(Long userId);


    /**
     * 특정 사용자의 모든 RefreshToken 삭제
     * 로그아웃 시 사용
     */
    @Modifying
    @Query("DELETE FROM RefreshToken rt WHERE rt.userId = :userId")
    void deleteByUserId(@Param("userId") Long userId);

    /**
     * 특정 토큰 삭제
     */
    @Modifying
    @Query("DELETE FROM RefreshToken rt WHERE rt.userRefreshToken = :token")
    void deleteByToken(@Param("token") String token);

    /**
     * 만료된 토큰들 조회
     * 배치 작업으로 정리할 때 사용
     */
    @Query("SELECT rt FROM RefreshToken rt WHERE rt.expiryDate < :now")
    List<RefreshToken> findExpiredTokens(@Param("now") LocalDateTime now);

    /**
     * 만료된 토큰들 일괄 삭제
     */
    @Modifying
    @Query("DELETE FROM RefreshToken rt WHERE rt.expiryDate < :now")
    void deleteExpiredTokens(@Param("now") LocalDateTime now);

    /**
     * 특정 시간 이전에 생성된 토큰들 삭제
     * 오래된 토큰 정리용
     */
    @Modifying
    @Query("DELETE FROM RefreshToken rt WHERE rt.createdAt < :beforeDate")
    void deleteOldTokens(@Param("beforeDate") LocalDateTime beforeDate);

    /**
     * 사용자별 활성 토큰 개수 조회
     */
    @Query("SELECT COUNT(rt) FROM RefreshToken rt WHERE rt.userId = :userId AND rt.expiryDate > :now")
    long countActiveTokensByUserId(@Param("userId") Long userId, @Param("now") LocalDateTime now);


    /**
     * 토큰 존재 여부 확인
     */
    boolean existsByUserRefreshToken(String token);

    /**
     * 특정 사용자의 유효한 토큰 존재 여부
     */
    @Query("SELECT CASE WHEN COUNT(rt) > 0 THEN true ELSE false END FROM RefreshToken rt WHERE rt.userId = :userId AND rt.expiryDate > :now")
    boolean existsValidTokenByUserId(@Param("userId") Long userId, @Param("now") LocalDateTime now);
}