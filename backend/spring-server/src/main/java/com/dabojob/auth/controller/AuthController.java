package com.dabojob.auth.controller;

import com.dabojob.auth.dto.SuccessResponse;
import com.dabojob.auth.dto.TokenResponse;
import com.dabojob.auth.dto.UserInfoResponse;
import com.dabojob.auth.service.AuthService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;


@Slf4j
@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;

    // 수정 코드
    @GetMapping("/login/{provider}")
    public void loginRedirect(@PathVariable String provider, HttpServletResponse response) throws IOException {
        if (!isValidProvider(provider)) {
            log.error("Unsupported OAuth provider: {}", provider);
            throw new IllegalArgumentException("Unsupported OAuth provider");
        }
        response.sendRedirect("/oauth2/authorization/" + provider);
    }


    @PostMapping("/refresh")
    public ResponseEntity<TokenResponse> refreshToken(HttpServletRequest request, HttpServletResponse response) {
        TokenResponse tokenResponse = authService.refreshTokenFromCookie(request, response);
        return ResponseEntity.ok(tokenResponse);
    }

    @PostMapping("/logout")
    public ResponseEntity<SuccessResponse> logout(Authentication authentication, HttpServletResponse response) {
        authService.logout(authentication, response);
        return ResponseEntity.ok(new SuccessResponse(true, "로그아웃되었습니다."));
    }


    @GetMapping("/me")
    public ResponseEntity<UserInfoResponse> getCurrentUser(Authentication authentication) {
        UserInfoResponse userInfo = authService.getCurrentUser(authentication);
        return ResponseEntity.ok(userInfo);
    }


    private boolean isValidProvider(String provider) {
        return provider.equals("google") || provider.equals("ssafy");
    }
}