package com.dabojob.auth.jwt;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Getter
@Setter
@Component
@ConfigurationProperties(prefix = "jwt")
public class JwtProperties {

    private String secretKey;
    private long accessTokenExpiration; // 30분 (밀리초)
    private long refreshTokenExpiration; // 14일 (밀리초)
    private String issuer;
}