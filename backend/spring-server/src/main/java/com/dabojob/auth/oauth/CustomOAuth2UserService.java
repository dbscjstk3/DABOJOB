package com.dabojob.auth.oauth;

import com.dabojob.global.enums.UserRole;
import com.dabojob.global.exception.DuplicatedEmailException;
import com.dabojob.user.repository.UserRepository;
import com.dabojob.user.entity.User;
import java.util.Map;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.oauth2.client.userinfo.DefaultOAuth2UserService;
import org.springframework.security.oauth2.client.userinfo.OAuth2UserRequest;
import org.springframework.security.oauth2.core.OAuth2AuthenticationException;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
@RequiredArgsConstructor
public class CustomOAuth2UserService extends DefaultOAuth2UserService {

    private final UserRepository userRepository;

    @Override
    @Transactional
    public OAuth2User loadUser(OAuth2UserRequest userRequest) throws OAuth2AuthenticationException {
        log.info("OAuth2 사용자 정보 로딩 시작");

        // 1. OAuth2UserService를 통해 사용자 정보 가져오기
        OAuth2User oAuth2User = super.loadUser(userRequest);

        // 2. OAuth 제공자 정보 추출
        String registrationId = userRequest.getClientRegistration().getRegistrationId();
        String userNameAttributeName = userRequest.getClientRegistration()
                .getProviderDetails()
                .getUserInfoEndpoint()
                .getUserNameAttributeName();

        log.info("OAuth2 제공자: {}, 사용자명 속성: {}", registrationId, userNameAttributeName);

        // 3. OAuth 제공자별 사용자 정보 추출
        OAuthUserInfo userInfo = getOAuthUserInfo(registrationId, oAuth2User.getAttributes());

        // 4. 사용자 저장 또는 업데이트
        User user = saveOrUpdate(userInfo);

        log.info("사용자 정보 처리 완료: ID={}, Email={}", user.getId(), user.getEmail());

        // 5. CustomOAuth2User 객체로 래핑하여 반환
        return new CustomOAuth2User(
                oAuth2User.getAuthorities(),
                oAuth2User.getAttributes(),
                userNameAttributeName,
                user
        );
    }

    /**
     * OAuth 제공자별 사용자 정보 추출
     */
    private OAuthUserInfo getOAuthUserInfo(String registrationId, Map<String, Object> attributes) {
        switch (registrationId.toLowerCase()) {
            case "google":
                return new GoogleUserInfo(attributes);
            case "ssafy":
                return new SsafyUserInfo(attributes);
            default:
                throw new OAuth2AuthenticationException("Unsupported OAuth provider: " + registrationId);
        }
    }

    /**
     * 사용자 정보 저장 또는 업데이트
     */

    private User saveOrUpdate(OAuthUserInfo userInfo) {
        // 1. 먼저 이메일로 기존 사용자 찾기
        Optional<User> existingUserByEmail = userRepository.findByEmail(userInfo.getEmail());

        if (existingUserByEmail.isPresent()) {
            User existingUser = existingUserByEmail.get();

            // 2. 같은 제공자인 경우 - 기존 로직대로 정보 업데이트
            if (existingUser.getProvider().equals(userInfo.getProvider())) {
                existingUser.updateProfile(userInfo.getEmail(), userInfo.getName());
                log.info("기존 사용자 정보 업데이트: {}", existingUser.getEmail());
                return userRepository.save(existingUser);
            }
            // 3. 다른 제공자인 경우 - 중복 계정 오류
            else {
                log.info("이미 사용 중인 이메일로 로그인 시도: {} ", existingUser.getEmail());
                throw new DuplicatedEmailException(userInfo.getEmail(), existingUser.getProvider());
            }
        }

        // 4. 신규 사용자 생성
        User newUser = User.builder()
                .email(userInfo.getEmail())
                .name(userInfo.getName())
                .provider(userInfo.getProvider())
                .providerId(userInfo.getProviderId())
                .role(determineUserRole(userInfo))
                .build();

        log.info("신규 사용자 생성: {}", newUser.getEmail());
        return userRepository.save(newUser);
    }

    /**
     * 사용자 권한 결정
     * 환경변수나 설정을 통해 관리자 계정 지정 가능
     */
    private UserRole determineUserRole(OAuthUserInfo userInfo) {
         String adminEmails = "jayeunpark0704@gmail.com"; //임시로 상수 설정


        if (adminEmails.equals(userInfo.getEmail())) {
            log.info("관리자 권한 부여: {}", userInfo.getEmail());
            return UserRole.ADMIN;
        }
        return UserRole.USER;

    }
}

