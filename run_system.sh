#!/bin/bash
# Ollama 기반 LLM 시스템 실행 스크립트

echo "🚀 Ollama 기반 LLM 시스템 시작..."

# 환경 체크
if [ ! -f ".env.private" ]; then
    echo "❌ .env.private 파일이 없습니다."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker가 설치되어 있지 않습니다."
        exit 1
    fi
fi

echo "🔧 시스템 설정 확인 중..."

# Docker Compose 실행
echo "📦 Docker 컨테이너 시작 중..."
echo "1. Redis 서버 시작..."
echo "2. Ollama 서버 시작..."
echo "3. 모델 다운로드 (최초 실행시 시간이 소요됩니다)..."
echo "4. 3개 API 서버 시작..."

docker-compose -f docker-compose.private.yml up -d --build

echo "⏳ 서버 초기화 대기 중..."
sleep 30

echo "🧪 시스템 테스트 실행 중..."

# Python 테스트 스크립트 실행
if command -v python3 &> /dev/null; then
    python3 test_ollama_system.py
elif command -v python &> /dev/null; then
    python test_ollama_system.py
else
    echo "⚠️  Python이 설치되어 있지 않습니다. 수동으로 테스트해주세요."
    echo ""
    echo "📋 서버 접속 정보:"
    echo "  - Standardizer: http://localhost:8000"
    echo "  - Summary: http://localhost:8100" 
    echo "  - News: http://localhost:8200"
    echo "  - Ollama: http://localhost:11434"
    echo ""
    echo "💡 헬스체크 명령어:"
    echo "  curl http://localhost:8000/health"
    echo "  curl http://localhost:8100/health"
    echo "  curl http://localhost:8200/health"
fi

echo ""
echo "🎯 시스템이 실행 중입니다!"
echo "📊 컨테이너 상태 확인: docker-compose -f docker-compose.private.yml ps"
echo "📋 로그 확인: docker-compose -f docker-compose.private.yml logs -f [service-name]"
echo "🛑 시스템 종료: docker-compose -f docker-compose.private.yml down"