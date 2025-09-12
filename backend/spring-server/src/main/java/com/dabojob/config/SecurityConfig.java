package com.dabojob.config;

import com.dabojob.auth.jwt.JwtAuthenticationFilter;
import com.dabojob.auth.oauth.CustomOAuth2UserService;
import com.dabojob.auth.oauth.OAuth2SuccessHandler;
import com.dabojob.global.exception.DuplicatedEmailException;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

import java.util.Arrays;
import java.util.List;

@Configuration
@EnableWebSecurity
@RequiredArgsConstructor
public class SecurityConfig {

    private final CustomOAuth2UserService customOAuth2UserService;
    private final OAuth2SuccessHandler oAuth2SuccessHandler;
    private final JwtAuthenticationFilter jwtAuthenticationFilter;

    @Value("${app.frontend.url}")
    private String frontendUrl; // 예: http://13.124.224.135 (끝에 / 없음)

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
                .csrf(AbstractHttpConfigurer::disable)
                .cors(cors -> cors.configurationSource(corsConfigurationSource()))
                .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                .authorizeHttpRequests(authz -> authz
                        // ✅ Actuator health/info 공개 (context-path 유무 모두 대비)
                        .requestMatchers(
                                "/actuator/health", "/actuator/health/**", "/actuator/info",
                                "/api/actuator/health", "/api/actuator/health/**", "/api/actuator/info"
                        ).permitAll()
                        // CORS preflight 허용
                        .requestMatchers(HttpMethod.OPTIONS, "/**").permitAll()

                        // 공개 엔드포인트
                        .requestMatchers("/", "/login", "/error", "/favicon.ico").permitAll()
                        .requestMatchers("/oauth2/**", "/api/auth/login/**").permitAll()
                        .requestMatchers("/api/auth/refresh", "/api/auth/refresh-cookie").permitAll()

                        // 인증 필요 엔드포인트
                        .requestMatchers("/api/auth/logout", "/api/auth/token-status", "/api/auth/revoke").authenticated()
                        .requestMatchers("/api/**").authenticated()

                        // 그 외
                        .anyRequest().permitAll()
                )
                .oauth2Login(oauth2 -> oauth2
                        .userInfoEndpoint(userInfo -> userInfo.userService(customOAuth2UserService))
                        .successHandler(oAuth2SuccessHandler)
                        .failureHandler((request, response, exception) -> {
                            String errorMessage = "oauth_failed";
                            if (exception instanceof DuplicatedEmailException) {
                                errorMessage = "duplicate_email";
                            }
                            response.sendRedirect(frontendUrl + "?error=" + errorMessage);
                        })
                )
                .exceptionHandling(exceptions -> exceptions
                        .authenticationEntryPoint((request, response, authException) -> {
                            response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
                            response.setContentType("application/json");
                            response.getWriter().write("{\"error\":\"Unauthorized\"}");
                        })
                )
                // ✅ JWT 필터는 UsernamePasswordAuthenticationFilter 앞에
                .addFilterBefore(jwtAuthenticationFilter, UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }

    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        // frontendUrl 과 정확히 일치해야 함 (프로토콜/포트 포함, 끝에 / 금지)
        CorsConfiguration configuration = new CorsConfiguration();
        configuration.setAllowedOrigins(List.of(frontendUrl));
        configuration.setAllowedMethods(Arrays.asList("GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"));
        configuration.setAllowedHeaders(List.of("*"));
        configuration.setAllowCredentials(true);
        configuration.setMaxAge(3600L);

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", configuration);
        return source;
    }
}
