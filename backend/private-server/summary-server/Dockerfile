# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Asia/Seoul \
    CUDA_VISIBLE_DEVICES="" \
    HF_HOME=/app/.cache/huggingface

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        git \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# Hugging Face 캐시 디렉토리 생성
RUN mkdir -p /app/.cache/huggingface

# 포트 노출
EXPOSE 8100

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=30s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8100/health || exit 1

# 서버 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8100", "--workers", "1"]
