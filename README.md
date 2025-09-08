# S13P21A402

모노레포 루트입니다. `services/spring-server` 하위에 스프링 부트 애플리케이션이 있습니다.

## 실행 (Docker)

1) 환경변수 준비
```
cp .env.example .env
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
- 테스트: Gradle test (작업 디렉터리: `services/spring-server`)
- 이미지: `services/spring-server/Dockerfile`로 빌드/푸시
