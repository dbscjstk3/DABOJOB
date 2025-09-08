package com.dabojob.auth.repository.entity;

import com.dabojob.global.repository.entity.BaseTimeEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Index;
import jakarta.persistence.Table;
import java.time.LocalDateTime;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "refresh_tokens", indexes = {
        @Index(name = "idx_user_id", columnList = "user_id"),
        @Index(name = "idx_user_refresh_token", columnList = "user_refresh_token"),
        @Index(name = "idx_expiry_date", columnList = "expiry_date")
})
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
@Builder
public class RefreshToken extends BaseTimeEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "refresh_token_id")
    private Long refreshTokenId;

    @Column(name = "user_id", nullable = false)
    private Long userId;

    @Column(name ="user_refresh_token", nullable = false, unique = true, length = 500)
    private String userRefreshToken;

    @Column(name = "expiry_date", nullable = false)
    private LocalDateTime expiryDate;


    /**
     * 토큰 만료 여부 확인
     */
    public boolean isExpired() {
        return LocalDateTime.now().isAfter(expiryDate);
    }

    /**
     * 토큰 갱신 (새로운 토큰과 만료시간 설정)
     */
    public void updateToken(String newToken, LocalDateTime newExpiryDate) {
        this.userRefreshToken = newToken;
        this.expiryDate = newExpiryDate;
    }


    /**
     * 토큰이 곧 만료되는지 확인 (1시간 이내)
     */
    public boolean isExpiringWithinHour() {
        LocalDateTime oneHourLater = LocalDateTime.now().plusHours(1);
        return expiryDate.isBefore(oneHourLater);
    }

    /**
     * 남은 유효시간(밀리초) 반환
     */
    public long getRemainingTimeMillis() {
        if (isExpired()) {
            return 0;
        }

        LocalDateTime now = LocalDateTime.now();
        return java.time.Duration.between(now, expiryDate).toMillis();
    }

    /**
     * 정적 팩토리 메서드: 새 리프레시 토큰 생성
     */
    public static RefreshToken create(Long userId, String token, LocalDateTime expiryDate) {
        return RefreshToken.builder()
                .userId(userId)
                .userRefreshToken(token)
                .expiryDate(expiryDate)
                .build();
    }

    /**
     * 정적 팩토리 메서드: 만료시간을 밀리초로 지정하여 생성
     */
    public static RefreshToken create(Long userId, String token, long expirationMillis) {
        LocalDateTime expiryDate = LocalDateTime.now().plusNanos(expirationMillis * 1_000_000);
        return create(userId, token, expiryDate);
    }
}