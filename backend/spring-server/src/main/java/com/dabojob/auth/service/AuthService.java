package com.dabojob.auth.service;

import com.dabojob.auth.dto.TokenResponse;
import com.dabojob.auth.dto.UserInfoResponse;
import com.dabojob.auth.jwt.JwtProperties;
import com.dabojob.auth.entity.RefreshToken;
import com.dabojob.global.exception.UnauthorizedException;
import com.dabojob.user.repository.UserRepository;
import com.dabojob.user.entity.User;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Slf4j
@RequiredArgsConstructor
public class AuthService {

    private final RefreshTokenService refreshTokenService;
    private final JwtProperties jwtProperties;
    private final CookieService cookieService;

    private final UserRepository userRepository;


    public TokenResponse refreshTokenFromCookie(HttpServletRequest request, HttpServletResponse response) {
        String refreshToken = cookieService.extractRefreshToken(request);
        if (refreshToken == null) {
            throw new UnauthorizedException("Refresh Token 쿠키가 없습니다.");
        }

        validateRefreshToken(refreshToken);

        // Access Token 갱신
        String newAccessToken = refreshTokenService.refreshAccessToken(refreshToken);
        long accessTokenExpiresIn = jwtProperties.getAccessTokenExpiration() / 1000;

        // Refresh Token도 함께 갱신 (Rolling Refresh Token 방식)
        RefreshToken newRefreshToken = refreshTokenService.renewRefreshToken(refreshToken);
        long refreshTokenExpiresIn = jwtProperties.getRefreshTokenExpiration() / 1000;

        // 새로운 토큰들을 쿠키로 설정
        cookieService.setAccessTokenCookie(response, newAccessToken, accessTokenExpiresIn);
        cookieService.setRefreshTokenCookie(response, newRefreshToken.getUserRefreshToken(), refreshTokenExpiresIn);

        log.debug("토큰 갱신 성공 (Rolling Refresh)");
        return TokenResponse.ofAccessToken(newAccessToken, accessTokenExpiresIn);
    }

    public void logout(Authentication authentication, HttpServletResponse response) {
        if (authentication != null && authentication.getPrincipal() != null) {
            Long userId = (Long) authentication.getPrincipal();
            refreshTokenService.revokeAllTokensByUser(userId);
            log.info("로그아웃 완료: userId={}", userId);
        }

        cookieService.clearAuthCookies(response);
    }


    private void validateRefreshToken(String refreshToken) {
        if (!refreshTokenService.validateRefreshToken(refreshToken)) {
            throw new UnauthorizedException("유효하지 않은 Refresh Token입니다.");
        }
    }

    @Transactional
    public UserInfoResponse getCurrentUser(Authentication authentication) {
        if (authentication == null || authentication.getPrincipal() == null) {
            throw new UnauthorizedException("인증이 필요합니다.");
        }

        Long userId = (Long) authentication.getPrincipal();
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new UnauthorizedException("사용자를 찾을 수 없습니다."));

        return UserInfoResponse.builder()
                .id(user.getId())
                .name(user.getName())
                .email(user.getEmail())
                .role(user.getRole().getRole())
                .provider(user.getProvider())
                .build();
    }
}