package com.dabojob.auth.oauth;

import com.dabojob.auth.jwt.JwtProperties;
import com.dabojob.auth.jwt.JwtService;
import com.dabojob.auth.service.CookieService;
import com.dabojob.auth.service.RefreshTokenService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.core.Authentication;
import org.springframework.security.web.authentication.SimpleUrlAuthenticationSuccessHandler;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.util.UriComponentsBuilder;

@Slf4j
@Component
@RequiredArgsConstructor
public class OAuth2SuccessHandler extends SimpleUrlAuthenticationSuccessHandler {

    private final JwtService jwtService;
    private final CookieService cookieService;
    private final RefreshTokenService refreshTokenService;
    private final JwtProperties jwtProperties;

    @Value("${app.frontend.url}")
    private String frontendUrl;

    @Override
    @Transactional
    public void onAuthenticationSuccess(HttpServletRequest request,
                                        HttpServletResponse response,
                                        Authentication authentication) throws IOException {

        log.info("OAuth 인증 성공 처리 시작");

        try {
            // 1. 인증된 사용자 정보 추출
            CustomOAuth2User oAuth2User = (CustomOAuth2User) authentication.getPrincipal();
            Long userId = oAuth2User.getUserId();

            log.debug("사용자 인증 성공: ID={}, Email={}, Provider={}",
                    userId, oAuth2User.getEmail(), oAuth2User.getProvider());

            // 2. JWT 토큰 생성
            String accessToken = jwtService.generateAccessToken(userId, oAuth2User.getUser().getRole());

            // 3. RefreshTokenService를 통해 Refresh Token 생성 및 저장
            var refreshToken = refreshTokenService.createRefreshToken(userId);

            log.info("JWT 토큰 생성 완료: userId={}", userId);

            // 4. CookieService를 통해 쿠키에 토큰 설정
            long accessTokenMaxAge = jwtProperties.getAccessTokenExpiration() / 1000; // 밀리초 -> 초
            long refreshTokenMaxAge = jwtProperties.getRefreshTokenExpiration() / 1000; // 밀리초 -> 초

            cookieService.setAccessTokenCookie(response, accessToken, accessTokenMaxAge);
            cookieService.setRefreshTokenCookie(response, refreshToken.getUserRefreshToken(), refreshTokenMaxAge);

            // 5. 프론트엔드로 리다이렉션 (쿠키 방식이므로 URL에 토큰 불포함)
            String redirectUrl = createRedirectUrl();

            log.debug("프론트엔드 리다이렉션: {}", redirectUrl);
            getRedirectStrategy().sendRedirect(request, response, redirectUrl);

        } catch (Exception e) {
            log.error("OAuth 성공 처리 중 오류 발생", e);

            // 오류 발생 시 에러 페이지로 리다이렉션
            String errorUrl = frontendUrl + "/auth/callback?error=token_generation_failed";
            getRedirectStrategy().sendRedirect(request, response, errorUrl);
        }
    }

    /**
     * 프론트엔드 리다이렉션 URL 생성 (쿠키 방식이므로 토큰은 URL에 포함하지 않음)
     */
    private String createRedirectUrl( ) {
        return UriComponentsBuilder.fromUriString(frontendUrl + "/auth/callback")
                .queryParam("success", "true")
                .encode() // 전체 URL을 인코딩
                .build()
                .toUriString();
    }
}