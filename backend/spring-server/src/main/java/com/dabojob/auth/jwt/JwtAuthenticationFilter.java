package com.dabojob.auth.jwt;

import com.dabojob.auth.service.CookieService;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

@Slf4j
@Component
@RequiredArgsConstructor
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private final JwtService jwtService;
    private final CookieService cookieService;

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {

        // 1. 쿠키에서 Access Token 추출.
        String token = cookieService.extractAccessToken(request);


        // 2. 토큰이 있고 유효한 경우 인증 설정
        if (token != null && jwtService.validateToken(token)) {
            try {
                // 3. 토큰에서 사용자 정보 추출
                Long userId = jwtService.getUserIdFromToken(token);
                String role = jwtService.getRoleFromToken(token);

                // 4. Spring Security 인증 객체 생성
                List<SimpleGrantedAuthority> authorities = List.of(new SimpleGrantedAuthority(role));
                UsernamePasswordAuthenticationToken authentication =
                        new UsernamePasswordAuthenticationToken(userId, null, authorities);
                authentication.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));

                // 5. SecurityContext에 인증 정보 설정
                SecurityContextHolder.getContext().setAuthentication(authentication);

            } catch (Exception e) {
                log.error("JWT 토큰 처리 중 오류 발생", e);
                SecurityContextHolder.clearContext();
            }
        }

        // 6. 다음 필터로 이동
        filterChain.doFilter(request, response);
    }


    /**
     * 인증이 필요 없는 경로는 필터를 건너뛰기
     */
    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        String path = request.getRequestURI();

        // 인증이 필요 없는 경로들
        return
                path.equals("/") ||
                path.equals("/error") ||
                path.equals("/favicon.ico") ||
                path.startsWith("/oauth2/") ||
                path.startsWith("/login/oauth2/");
    }
}