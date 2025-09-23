package com.dabojob.auth.oauth;

import com.dabojob.global.exception.DuplicatedEmailException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.oauth2.core.OAuth2AuthenticationException;
import org.springframework.security.web.authentication.SimpleUrlAuthenticationFailureHandler;
import org.springframework.stereotype.Component;


@Component
@RequiredArgsConstructor
@Slf4j
public class OAuth2FailureHandler extends SimpleUrlAuthenticationFailureHandler {

    @Value("${app.frontend.url}")
    private String frontendUrl;

    @Override
    public void onAuthenticationFailure(HttpServletRequest request,
                                        HttpServletResponse response,
                                        AuthenticationException exception) throws IOException {

        log.error("OAuth 인증 실패: {}", exception.getMessage(), exception);

        String errorCode = determineErrorCode(exception);
        String redirectUrl = frontendUrl + "/auth/callback?error=" + errorCode;

        getRedirectStrategy().sendRedirect(request, response, redirectUrl);
    }

    private String determineErrorCode(AuthenticationException exception) {
        if (exception instanceof DuplicatedEmailException) {
            return "duplicated_email";
        } else if (exception instanceof OAuth2AuthenticationException) {
            return "oauth_provider_error";
        } else {
            return "authentication_failed";
        }
    }
}
