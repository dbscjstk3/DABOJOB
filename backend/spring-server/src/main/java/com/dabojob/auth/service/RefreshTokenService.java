package com.dabojob.auth.service;

import com.dabojob.auth.jwt.JwtService;
import com.dabojob.auth.repository.RefreshTokenRepository;
import com.dabojob.auth.entity.RefreshToken;
import com.dabojob.global.exception.UnauthorizedException;
import com.dabojob.user.repository.UserRepository;
import com.dabojob.user.entity.User;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional
public class RefreshTokenService {

    private final RefreshTokenRepository refreshTokenRepository;
    private final JwtService jwtService;
    private final UserRepository userRepository;

    /**
     * 새로운 Refresh Token 생성 및 저장
     */
    @Transactional
    public RefreshToken createRefreshToken(Long userId) {
        // 기존 사용자의 모든 토큰 삭제 (한 사용자당 하나의 토큰만 유지)
        refreshTokenRepository.deleteByUserId(userId);

        // 새 토큰 생성
        String tokenValue = jwtService.generateRefreshToken(userId);
        RefreshToken refreshToken = RefreshToken.create(
                userId,
                tokenValue,
                LocalDateTime.now().plusDays(14) // 14일 후 만료
        );

        RefreshToken savedToken = refreshTokenRepository.save(refreshToken);
        log.info("새 Refresh Token 생성: userId={}, tokenId={}", userId, savedToken.getId());

        return savedToken;
    }


    /**
     * 토큰 유효성 검증
     */
    @Transactional(readOnly = true)
    public boolean validateRefreshToken(String token) {
        Optional<RefreshToken> refreshTokenOpt = refreshTokenRepository.findByUserRefreshToken(token);

        if (refreshTokenOpt.isEmpty()) {
            log.debug("존재하지 않는 Refresh Token: {}", token);
            return false;
        }

        RefreshToken refreshToken = refreshTokenOpt.get();

        if (refreshToken.isExpired()) {
            log.debug("만료된 Refresh Token: userId={}, expiry={}",
                    refreshToken.getUserId(), refreshToken.getExpiryDate());
            // 만료된 토큰 즉시 삭제
            refreshTokenRepository.delete(refreshToken);
            return false;
        }

        return true;
    }

    /**
     * Refresh Token을 사용하여 새 Access Token 발급
     */
    @Transactional
    public String refreshAccessToken(String refreshTokenValue) {
        RefreshToken refreshToken = refreshTokenRepository.findByUserRefreshToken(refreshTokenValue)
                .orElseThrow(() -> new UnauthorizedException("유효하지 않은 Refresh Token입니다."));

        if (refreshToken.isExpired()) {
            refreshTokenRepository.delete(refreshToken);
            throw new UnauthorizedException("만료된 Refresh Token입니다.");
        }

        Long userId = refreshToken.getUserId();
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new UnauthorizedException("사용자를 찾을 수 없습니다."));

        return jwtService.generateAccessToken(userId, user.getRole());
    }

    /**
     * Refresh Token 갱신 (만료 임박 시)
     */
    @Transactional
    public RefreshToken renewRefreshToken(String oldTokenValue) {
        RefreshToken oldToken = refreshTokenRepository.findByUserRefreshToken(oldTokenValue)
                .orElseThrow(() -> new IllegalArgumentException("유효하지 않은 Refresh Token입니다."));

        if (oldToken.isExpired()) {
            refreshTokenRepository.delete(oldToken);
            throw new IllegalArgumentException("만료된 Refresh Token입니다.");
        }

        // 새 토큰 생성
        String newTokenValue = jwtService.generateRefreshToken(oldToken.getUserId());
        oldToken.updateToken(newTokenValue, LocalDateTime.now().plusDays(14));

        RefreshToken updatedToken = refreshTokenRepository.save(oldToken);
        log.info("Refresh Token 갱신 완료: userId={}", oldToken.getUserId());

        return updatedToken;
    }

    /**
     * 특정 사용자의 모든 Refresh Token 삭제 (로그아웃)
     */
    @Transactional
    public void revokeAllTokensByUser(Long userId) {
        int deletedCount = refreshTokenRepository.findByUserId(userId).size();
        refreshTokenRepository.deleteByUserId(userId);
        log.info("사용자 토큰 전체 삭제: userId={}, count={}", userId, deletedCount);
    }

    /**
     * 특정 Refresh Token 삭제
     */
    @Transactional
    public void revokeToken(String token) {
        refreshTokenRepository.deleteByToken(token);
        log.info("Refresh Token 삭제 완료: token={}", token);
    }

    /**
     * 사용자의 활성 토큰 개수 조회
     */
    @Transactional(readOnly = true)
    public long countActiveTokensByUser(Long userId) {
        return refreshTokenRepository.countActiveTokensByUserId(userId, LocalDateTime.now());
    }



    /**
     * 만료된 토큰 일괄 정리 (스케줄러)
     * 매일 새벽 2시에 실행
     */
    @Scheduled(cron = "0 0 2 * * *")
    public void cleanupExpiredTokens() {
        LocalDateTime now = LocalDateTime.now();
        List<RefreshToken> expiredTokens = refreshTokenRepository.findExpiredTokens(now);

        if (!expiredTokens.isEmpty()) {
            refreshTokenRepository.deleteExpiredTokens(now);
            log.info("만료된 토큰 정리 완료: count={}", expiredTokens.size());
        }
    }

}