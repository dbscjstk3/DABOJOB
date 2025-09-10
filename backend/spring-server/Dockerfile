# Build stage
FROM gradle:8.10.2-jdk17-alpine AS builder
WORKDIR /workspace

# Gradle 캐시 활용을 위해 먼저 래퍼/설정 복사
COPY build.gradle settings.gradle .
COPY gradle gradle
COPY gradlew gradlew

# ⬇︎ 실행권한 + 윈도우 줄끝 제거(있다면)
RUN chmod +x gradlew && sed -i 's/\r$//' gradlew

# 의존성 프리페치 (소스 없이도 종속성 캐시)
RUN ./gradlew --no-daemon dependencies || true

# 소스 복사 후 빌드
COPY src src
RUN ./gradlew --no-daemon clean bootJar

# Runtime stage
FROM eclipse-temurin:17-jre-alpine
ENV TZ=Asia/Seoul
WORKDIR /app

# 빌드 산출물 복사
COPY --from=builder /workspace/build/libs/*.jar app.jar

# 애플리케이션 포트 (필요 시 docker run -p 로 매핑)
EXPOSE 8080

# JAVA_OPTS로 JVM 옵션 주입 가능하게
ENV JAVA_OPTS=""

ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar /app/app.jar"]
