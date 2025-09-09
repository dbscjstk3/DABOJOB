## Spring Boot Service (Dockerized)

이 저장소는 Spring Boot 단일 서비스용 저장소입니다. 다중 서비스(FastAPI, DB 등) 오케스트레이션은 상위 인프라/모노 저장소에서 `docker-compose.yml`로 관리합니다.

### 요구사항
- JDK 17
- Gradle Wrapper 포함
- Docker

### 로컬 실행
```bash
./gradlew bootRun
```

### Docker 이미지 빌드/실행
```bash
# 이미지 빌드
docker build -t your-registry/your-app:local .

# 실행 (환경변수로 설정 주입)
docker run --rm -p 8080:8080 \
  -e SPRING_DATASOURCE_URL="jdbc:mysql://host.docker.internal:3306/app?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=Asia/Seoul" \
  -e SPRING_DATASOURCE_USERNAME="root" \
  -e SPRING_DATASOURCE_PASSWORD="password" \
  your-registry/your-app:local
```

### 환경변수
- `SERVER_PORT` (기본 8080)
- `SPRING_DATASOURCE_URL`
- `SPRING_DATASOURCE_USERNAME`
- `SPRING_DATASOURCE_PASSWORD`
- `SPRING_JPA_HIBERNATE_DDL_AUTO` (none, validate, update, create, create-drop)
- `SPRING_JPA_SHOW_SQL` (true/false)
- `SPRING_JPA_FORMAT_SQL` (true/false)

### Compose 관리 가이드
- 이 저장소에는 `docker-compose.yml`을 두지 않습니다.
- 상위 저장소에서 다음과 같이 서비스 조합을 정의합니다.
```yaml
services:
  spring:
    image: your-registry/your-app:${TAG}
    environment:
      - SPRING_DATASOURCE_URL=mysql jdbc url
      - SPRING_DATASOURCE_USERNAME
      - SPRING_DATASOURCE_PASSWORD
  fastapi:
    image: your-registry/your-fastapi:${TAG}
  mysql:
    image: mysql:8
```
