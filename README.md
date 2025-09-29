# 📊 DABOJOB - AI 기반 취준생 기업 정보 통합 플랫폼

[![Spring Boot](https://img.shields.io/badge/Spring%20Boot-3.5.5-brightgreen.svg)](https://spring.io/projects/spring-boot)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8-3178C6.svg)](https://www.typescriptlang.org/)
[![AWS](https://img.shields.io/badge/AWS-EC2%20%7C%20S3-FF9900.svg)](https://aws.amazon.com/)

> **취준생을 위한 AI 기반 기업 공시자료 & 뉴스 통합 분석 플랫폼**
>
> 방대한 사업보고서를 읽을 필요 없이, DART 보고서 요약으로 한번에!

![13기_특화PJT_영상_포트폴리오_A402](<13기_특화PJT_영상 포트폴리오_A402.gif>)

---

## 🎯 프로젝트 개요

### 왜 만들었나요?

취준생들은 지원 기업 분석을 위해 DART 전자공시를 봅니다. 하지만:
- 📚 **사업보고서는 평균 300페이지 이상** → 시간이 너무 오래 걸림
- 🤯 **전문 용어 투성이** → 비전문가가 이해하기 어려움
- 📰 **최신 뉴스까지 찾아봐야 함** → 정보가 분산되어 있음

**우리의 솔루션**: AI가 공시자료와 뉴스를 자동으로 수집/분석/요약하여, 취준생에게 꼭 필요한 정보만 직관적으로 제공합니다.

---

## ✨ 핵심 기능

### 1️⃣ 공채 달력 모드
- 📅 이번 달/다음 달 채용 공고를 달력 형태로 시각화
- 🔍 관심 기업 빠른 찾기 & 북마크 기능

### 2️⃣ 기업 상세 정보 모드
- 📊 **AI 요약 보고서**: 사업 개요, 재무 지표, 성장 전략 등 5개 핵심 섹션
- 📰 **실시간 뉴스 요약**: 기업 관련 최신 뉴스 자동 수집 & 요약
- 🏷️ **해시태그 추출**: AI가 뽑은 키워드로 빠른 정보 스캔
- 🔎 **ElasticSearch 기반 검색**: 기업명, 키워드로 즉시 검색
- 🔐 **OAuth2 소셜 로그인**: Google, SSAFY 계정 연동

### 3️⃣ 자동화된 데이터 파이프라인
사람인 API → DART API → 표준화 → AI 요약 → 뉴스 수집 → 통합 저장 → 서비스 제공

---

## 🏗️ 시스템 아키텍처

### 전체 구조도
```
┌─────────────┐          ┌──────────────────────────────────────┐
│   사용자    │◄────────► │         Main Server (EC2)            │
│  (React)    │          │  - Spring Boot + JWT Auth            │
└─────────────┘          │  - Redis Cache                       │
                         │  - MySQL (RDS)                       │
                         │  - ElasticSearch                     │
                         └───────────────┬──────────────────────┘
                                         │ S3 기반 상태 관리
                         ┌───────────────▼──────────────────────┐
                         │      Private Server Cluster (EC2)    │
                         ├──────────────────────────────────────┤
                         │  ┌──────────────────────────────┐    │
                         │  │ Standardizer Server          │    │
                         │  │ - 사람인 API → DART 매칭       │    │
                         │  │ - 공시자료 표준화 (LLM)         │    │
                         │  └──────────┬───────────────────┘    │
                         │             │ Redis Stream           │
                         │  ┌──────────▼───────────────────┐    │
                         │  │ Summary Server               │    │
                         │  │ - AI 요약 (5개 섹션)           │    │
                         │  │ - 해시태그 추출                │    │
                         │  └──────────┬───────────────────┘    │
                         │             │                        │
                         │  ┌──────────▼───────────────────┐    │
                         │  │ News Summary Server          │    │
                         │  │ - 뉴스 API 수집               │    │
                         │  │ - 뉴스 요약 (LLM)             │    │
                         │  │ - S3 업로드 (READY 상태)       │    │
                         │  └──────────────────────────────┘    │
                         └──────────────────────────────────────┘
```

### 데이터 플로우 (상태 기반 처리)

1. Standardizer: 원시 데이터 수집 & 표준화 → EC2 Local 저장
2. Summary: 표준화 데이터 요약 → Redis Stream으로 전달
3. News Summary: 뉴스 수집 & 통합 → S3에 READY 상태로 업로드
4. Main Server: S3 폴링 → READY 파일 감지 → MySQL 저장 → COMPLETE 변경
5. 사용자 요청 시 MySQL 조회 & Redis 캐싱으로 빠른 응답

---

## 🛠️ 기술 스택

### Backend
| 영역 | 기술 | 선택 이유 |
|------|------|-----------|
| **Main API** | Spring Boot 3.5.5, Java 17 | 엔터프라이즈급 안정성 & 확장성 |
| **AI 처리** | Python 3.9+, FastAPI | LLM 통합에 최적화된 생태계 |
| **DB** | MySQL 8.0.42, MongoDB 7.0.14 | 정형/비정형 데이터 모두 지원 |
| **캐싱** | Redis 7-alpine | 검색 결과 응답 속도 향상 |
| **작업 큐** | Redis Stream | 비동기 AI 처리 작업 분산 |
| **검색** | ElasticSearch | 전문 검색 & 자동완성 지원 |
| **인증** | Spring Security + OAuth2 + JWT | Google, SSAFY 소셜 로그인 |
| **LLM** | Ollama | 로컬 LLM 서비스 |

### Frontend
- **React 19**: 최신 컴포넌트 기반 SPA
- **TypeScript 5.8**: 타입 안전성 보장
- **TanStack Router**: 타입 세이프 라우팅
- **TanStack Query**: 서버 상태 관리
- **Vite**: 빠른 개발 환경
- **Tailwind CSS**: 유틸리티 기반 스타일링
- **Zustand**: 클라이언트 상태 관리

### Infrastructure
- **AWS EC2**: Main Server (1대) + Private Server (1대)
- **AWS S3**: 대용량 공시자료 & 요약 결과 저장
- **Docker Compose**: 멀티 컨테이너 오케스트레이션
- **Caddy**: 리버스 프록시 & HTTPS 자동화

### AI & Data
- **LLM**: Ollama (로컬 LLM 서비스)
- **DART API**: 전자공시 원문 수집
- **사람인 API**: 채용 공고 수집
- **뉴스 API**: 실시간 기업 뉴스 수집

---

## 📦 프로젝트 구조
```
├── backend/
│   ├── spring-server/            # Spring Boot (Main API)
│   │   ├── src/main/java/com/dabojob/
│   │   │   ├── auth/             # OAuth2 인증
│   │   │   ├── jobposting/       # 채용공고 관리
│   │   │   ├── summary/          # AI 요약 서비스
│   │   │   └── sync/             # 데이터 동기화
│   │   ├── build.gradle
│   │   └── application.yml
│   └── private-server/
│       ├── standardizer-server/  # FastAPI (표준화)
│       ├── summary-server/       # FastAPI (AI 요약)
│       └── news-summary-server/  # FastAPI (뉴스 처리)
├── frontend/
│   ├── src/
│   │   ├── components/          # 컴포넌트 (Atomic Design)
│   │   │   ├── calendar/        # 달력 관련
│   │   │   ├── calendar-detail/ # 상세 페이지
│   │   │   └── admin/           # 관리자 페이지
│   │   ├── pages/               # 페이지 컴포넌트
│   │   └── services/            # API 호출 로직
│   ├── package.json
│   └── vite.config.ts
├── exec/
│   ├── 1_빌드_및_배포_가이드.md
│   └── 2_외부_서비스_정보.md
├── docker-compose.full.yml      # 전체 시스템
├── docker-compose.spring.yml    # Spring 서버만
├── docker-compose.private.yml   # Private 서버들
└── Caddyfile                    # 리버스 프록시 설정
```

---

## 🚀 빠른 시작

### 사전 요구사항
```bash
# 필수 설치
- Docker 20.10+
- Docker Compose 2.0+
- Node.js 18+
- Python 3.9+
- Java 17+
- Gradle 8.14.3+

# API 키 발급 필요
- Google OAuth2 클라이언트 ID/Secret
- SSAFY OAuth2 설정
- DART OpenAPI 키
- 사람인 API 키
- 뉴스 API 키
```

### 1. 프로젝트 클론
```bash
git clone [repository-url]
cd S13P21A402
```

### 2. 환경 변수 설정
```bash
# Spring 서버용 환경 변수
cp .env.spring.example .env.spring
# Private 서버용 환경 변수
cp .env.private.example .env.private

# 각 .env 파일에 실제 API 키 및 설정 입력
```

### 3. 전체 시스템 실행 (권장)
```bash
# 전체 시스템 (Spring + Private Servers + DBs + Ollama)
docker-compose -f docker-compose.full.yml up -d

# 실행 확인
docker-compose -f docker-compose.full.yml ps
```

### 4. 개별 서비스 실행
```bash
# Spring 서버만 실행
docker-compose -f docker-compose.spring.yml up -d

# Private 서버들만 실행
docker-compose -f docker-compose.private.yml up -d
```

### 5. 프론트엔드 개발 서버
```bash
cd frontend
npm install
npm run dev
```

### 6. 접속 정보
- **프론트엔드**: http://localhost:5173
- **Spring API**: http://localhost:8080
- **Standardizer**: http://localhost:8000
- **Summary Server**: http://localhost:8100
- **News Summary**: http://localhost:8200
- **Ollama**: http://localhost:11434

---

## 📋 주요 API 엔드포인트

### 인증
- `POST /api/auth/login` - OAuth2 로그인
- `POST /api/auth/refresh` - 토큰 갱신

### 채용공고
- `GET /api/job-postings` - 채용공고 목록
- `GET /api/job-postings/search` - 기업 검색 (ElasticSearch)
- `GET /api/job-postings/{id}` - 채용공고 상세

### AI 요약
- `GET /api/summaries/{companyId}` - 기업 AI 요약 조회
- `POST /api/summaries/generate` - AI 요약 생성 (관리자)

---

## 🔧 개발 가이드

### 빌드 및 배포
자세한 내용은 [`exec/1_빌드_및_배포_가이드.md`](./exec/1_빌드_및_배포_가이드.md) 참조

### 외부 서비스 연동
OAuth2, API 키 설정은 [`exec/2_외부_서비스_정보.md`](./exec/2_외부_서비스_정보.md) 참조

### 아키텍처 상세
시스템 구조와 데이터 플로우에 대한 상세한 설명은 프로젝트 내 문서를 참조하세요.

---

## 🏆 프로젝트 특징

- **🚀 성능**: Redis 캐싱으로 검색 응답 속도 최적화
- **🔒 보안**: OAuth2 + JWT 기반 안전한 인증
- **🎯 사용성**: 직관적인 달력 UI와 AI 요약으로 정보 접근성 향상
- **⚡ 확장성**: 마이크로서비스 아키텍처로 개별 서비스 독립 운영
- **🤖 AI 통합**: Ollama 기반 로컬 LLM으로 데이터 보안 강화

---

## 👥 팀 정보

**SSAFY 13기 2학기 빅데이터 분산 프로젝트**
**Team S13P21A402**

| 이름 | 역할 | 담당 업무 |
|------|------|-----------|
| 김미림 | Backend | News Server - 뉴스 API 및 크롤링, AI 요약, S3 관리 및 데이터 저장 |
| 이영우 | DevOps | 인프라 - EC2 설정, Docker, 서버 간 통신, Jenkins |
| 이종환 | Backend | Main Server - Auth, User 관리, 스케줄러, Elastic Search, Redis |
| 이지민 | Backend | Standardizer/Summary Server - AI 요약 및 파인튜닝, 해시태그 추출, Redis Stream로 Job Queue 구축 |
| 박재은 | Frontend | 달력 상세, 검색 상세, 관리자 페이지의 매핑 실패/성공 |
| 윤현석 | Frontend | 로그인, 메인 페이지(공채 달력, 관리자 달력) |

