# S13P21A402

모노레포 루트입니다. `backend/spring-server` 하위에 스프링 부트 애플리케이션이 있습니다.

## 실행 (Docker)

1) 환경변수 준비 (두 개의 env 파일 사용)

아래 두 파일을 프로젝트 루트에 생성하세요:

- `.env.spring` (스프링 서버용)
- `.env.private` (프라이빗 서버 3종용: standardizer, summary, news-summary)

예시 내용은 다음을 참고하세요.

`.env.spring` 예시:
```
SERVER_PORT=8080
JAVA_OPTS=

# DB
SPRING_DATASOURCE_URL=jdbc:mysql://db:3306/app?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=Asia/Seoul
SPRING_DATASOURCE_USERNAME=app
SPRING_DATASOURCE_PASSWORD=app
SPRING_DATASOURCE_DRIVER=com.mysql.cj.jdbc.Driver
SPRING_DATASOURCE_IDLE_TIMEOUT=300000
SPRING_DATASOURCE_MIN_IDLE=3
SPRING_DATASOURCE_MAX_POOL_SIZE=5
SPRING_DATASOURCE_CONNECTION_TIMEOUT=600000

# JPA
SPRING_JPA_OPEN_IN_VIEW=false
SPRING_JPA_HIBERNATE_DDL_AUTO=none
SPRING_JPA_SHOW_SQL=false
SPRING_JPA_FORMAT_SQL=false

# OAuth2
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
SSAFY_CLIENT_ID=
SSAFY_CLIENT_SECRET=
SSAFY_AUTHORIZATION_URI=https://project.ssafy.com/oauth/sso-check
SSAFY_TOKEN_URI=https://project.ssafy.com/ssafy/oauth2/token
SSAFY_USER_INFO_URI=https://project.ssafy.com/ssafy/resources/userInfo
SSAFY_USER_NAME_ATTRIBUTE=userId

# JWT
JWT_SECRET_KEY=
JWT_ACCESS_TOKEN_EXPIRATION=1800000
JWT_REFRESH_TOKEN_EXPIRATION=1209600000
JWT_ISSUER=dabojob-app

# App
APP_FRONTEND_URL=http://localhost:5173
```

`.env.private` 예시:
```
# 컨테이너 외부 노출 포트 (원하면 변경)
STANDARDIZER_PORT=8000
SUMMARY_PORT=8100
NEWS_SUMMARY_PORT=8200

# 공통
TZ=Asia/Seoul
```

2) 빌드/기동
```
docker compose up -d --build
```

3) 확인
- 웹: http://localhost:8080/health
- DB(MySQL): localhost:3306 (컨테이너 내부는 db:3306)

## GitLab CI
- 루트 `.gitlab-ci.yml` 사용
- 테스트: Gradle test (작업 디렉터리: `backend/spring-server`)
- 이미지: `backend/spring-server/Dockerfile`로 빌드/푸시
