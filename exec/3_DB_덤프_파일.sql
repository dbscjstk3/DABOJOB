-- ===================================================================
-- DABOJOB 프로젝트 데이터베이스 스키마 및 초기 데이터
-- 작성일: 2024-12-29
-- 버전: 1.0
-- 호환성: MySQL 8.0+
-- ===================================================================

-- 데이터베이스 생성
CREATE DATABASE IF NOT EXISTS maindb
DEFAULT CHARACTER SET utf8mb4
COLLATE utf8mb4_general_ci;

CREATE DATABASE IF NOT EXISTS private_app
DEFAULT CHARACTER SET utf8mb4
COLLATE utf8mb4_general_ci;

USE maindb;

-- ===================================================================
-- 1. 사용자 관리 테이블
-- ===================================================================

-- 사용자 테이블
CREATE TABLE users (
    id BIGINT NOT NULL AUTO_INCREMENT,
    email VARCHAR(255) NOT NULL COMMENT '사용자 이메일',
    name VARCHAR(255) NOT NULL COMMENT '사용자 이름',
    role ENUM('USER', 'ADMIN') NOT NULL DEFAULT 'USER' COMMENT '사용자 권한',
    provider VARCHAR(50) NOT NULL COMMENT 'OAuth 제공자 (google, ssafy)',
    provider_id VARCHAR(255) NOT NULL COMMENT 'OAuth 제공자 사용자 ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_users_provider (provider, provider_id),
    INDEX idx_users_email (email),
    INDEX idx_users_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
COMMENT='사용자 정보 테이블';

-- 리프레시 토큰 테이블
CREATE TABLE refresh_tokens (
    id BIGINT NOT NULL AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    token VARCHAR(500) NOT NULL COMMENT 'JWT 리프레시 토큰',
    expires_at TIMESTAMP NOT NULL COMMENT '만료 시간',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_refresh_tokens_token (token),
    INDEX idx_refresh_tokens_user_id (user_id),
    INDEX idx_refresh_tokens_expires (expires_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
COMMENT='JWT 리프레시 토큰 관리 테이블';

-- ===================================================================
-- 2. 회사 및 채용 관련 테이블
-- ===================================================================

-- 회사 테이블
CREATE TABLE companies (
    id BIGINT NOT NULL COMMENT '회사 고유 ID (DART 코드 등)',
    name VARCHAR(255) NOT NULL COMMENT '회사명',
    scale ENUM('STARTUP', 'SMALL', 'MEDIUM', 'LARGE', 'UNKNOWN') NOT NULL DEFAULT 'UNKNOWN' COMMENT '회사 규모',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_companies_name (name),
    INDEX idx_companies_scale (scale),
    FULLTEXT KEY ft_companies_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
COMMENT='회사 정보 테이블';

-- 직무 분야 테이블
CREATE TABLE job_sectors (
    id BIGINT NOT NULL AUTO_INCREMENT,
    sector_name VARCHAR(100) NOT NULL COMMENT '직무 분야명',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_job_sectors_name (sector_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
COMMENT='직무 분야 테이블';

-- 채용공고 테이블
CREATE TABLE job_postings (
    id BIGINT NOT NULL COMMENT '채용공고 고유 ID',
    company_id BIGINT NOT NULL,
    job_sector_id BIGINT NOT NULL,
    title VARCHAR(500) COMMENT '채용공고 제목',
    url VARCHAR(1000) COMMENT '원본 URL',
    career_info ENUM('ENTRY_LEVEL', 'JUNIOR', 'MID_LEVEL', 'SENIOR', 'EXECUTIVE', 'UNKNOWN') NOT NULL DEFAULT 'UNKNOWN' COMMENT '경력 요구사항',
    posting_date DATE COMMENT '공고 등록일',
    deadline_date DATE COMMENT '마감일',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_job_postings_company (company_id),
    INDEX idx_job_postings_sector (job_sector_id),
    INDEX idx_job_postings_posting_date (posting_date),
    INDEX idx_job_postings_deadline_date (deadline_date),
    INDEX idx_job_postings_career (career_info),
    INDEX idx_job_postings_company_posting_date (company_id, posting_date),
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    FOREIGN KEY (job_sector_id) REFERENCES job_sectors(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
COMMENT='채용공고 정보 테이블';

-- 채용공고 문서 (Elasticsearch 연동용)
CREATE TABLE job_posting_documents (
    id BIGINT NOT NULL AUTO_INCREMENT,
    job_posting_id BIGINT NOT NULL,
    content TEXT COMMENT '채용공고 상세 내용',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_job_posting_documents_posting (job_posting_id),
    FULLTEXT KEY ft_job_posting_documents_content (content),
    FOREIGN KEY (job_posting_id) REFERENCES job_postings(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
COMMENT='채용공고 상세 내용 (검색용)';

-- ===================================================================
-- 3. 뉴스 및 분석 관련 테이블
-- ===================================================================

-- 해시태그 테이블
CREATE TABLE hashtags (
    id BIGINT NOT NULL AUTO_INCREMENT,
    tag_name VARCHAR(100) NOT NULL COMMENT '해시태그명',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_hashtags_name (tag_name),
    INDEX idx_hashtags_name (tag_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
COMMENT='뉴스 분류용 해시태그 테이블';

-- 요약-해시태그 연결 테이블
CREATE TABLE summary_hashtags (
    id BIGINT NOT NULL AUTO_INCREMENT,
    company_id BIGINT NOT NULL,
    hashtag_id BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_summary_hashtags_company_hashtag (company_id, hashtag_id),
    INDEX idx_summary_hashtags_company (company_id),
    INDEX idx_summary_hashtags_hashtag (hashtag_id),
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    FOREIGN KEY (hashtag_id) REFERENCES hashtags(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
COMMENT='회사별 해시태그 연결 테이블';

-- 뉴스 테이블
CREATE TABLE news (
    id BIGINT NOT NULL AUTO_INCREMENT,
    summary_hashtag_id BIGINT COMMENT '연결된 요약-해시태그 ID',
    title VARCHAR(500) COMMENT '뉴스 제목',
    content TEXT COMMENT '뉴스 내용',
    url VARCHAR(1000) COMMENT '뉴스 원문 URL',
    posting_date DATE COMMENT '뉴스 발행일',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_news_summary_hashtag (summary_hashtag_id),
    INDEX idx_news_posting_date (posting_date),
    INDEX idx_news_title (title(100)),
    INDEX idx_news_posting_date_summary (posting_date, summary_hashtag_id),
    FULLTEXT KEY ft_news_title_content (title, content),
    FOREIGN KEY (summary_hashtag_id) REFERENCES summary_hashtags(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
COMMENT='뉴스 정보 테이블';

-- 회사 분석 요약 테이블
CREATE TABLE company_analysis_summaries (
    id BIGINT NOT NULL AUTO_INCREMENT,
    company_id BIGINT COMMENT '분석 대상 회사 ID',
    business_overview TEXT COMMENT '사업개요',
    products_service TEXT COMMENT '주요 제품/서비스',
    sales_contracts TEXT COMMENT '영업 및 계약 현황',
    rnd_activities TEXT COMMENT 'R&D 연구개발 활동',
    other_notes TEXT COMMENT '기타 특이사항',
    status ENUM('CREATED', 'UPDATED', 'FINISHED') NOT NULL DEFAULT 'CREATED' COMMENT '분석 상태',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_company_analysis_company (company_id),
    INDEX idx_company_analysis_status (status),
    INDEX idx_company_analysis_company_status (company_id, status),
    FULLTEXT KEY ft_company_analysis_content (business_overview, products_service, sales_contracts, rnd_activities, other_notes),
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
COMMENT='AI 기반 회사 분석 요약 테이블';

-- ===================================================================
-- 4. 초기 데이터 삽입
-- ===================================================================

-- 직무 분야 기본 데이터
INSERT INTO job_sectors (sector_name) VALUES
('웹개발'),
('앱개발'),
('게임개발'),
('시스템/네트워크'),
('인공지능/머신러닝'),
('데이터분석'),
('정보보안'),
('DevOps/클라우드'),
('QA/테스팅'),
('기획/PM'),
('디자인'),
('기타');

-- 샘플 회사 데이터
INSERT INTO companies (id, name, scale) VALUES
(1, '삼성전자', 'LARGE'),
(2, 'SK하이닉스', 'LARGE'),
(3, 'LG전자', 'LARGE'),
(4, '네이버', 'LARGE'),
(5, '카카오', 'LARGE'),
(6, '토스', 'MEDIUM'),
(7, '당근마켓', 'MEDIUM'),
(8, '크래프톤', 'MEDIUM'),
(9, '라인플러스', 'MEDIUM'),
(10, '배달의민족', 'MEDIUM');

-- 샘플 해시태그 데이터
INSERT INTO hashtags (tag_name) VALUES
('반도체'),
('전자제품'),
('모바일'),
('AI'),
('클라우드'),
('게임'),
('핀테크'),
('커머스'),
('플랫폼'),
('스타트업');

-- 샘플 채용공고 데이터
INSERT INTO job_postings (id, company_id, job_sector_id, title, career_info, posting_date, deadline_date) VALUES
(1, 1, 1, '삼성전자 웹 프론트엔드 개발자 모집', 'JUNIOR', '2024-12-01', '2024-12-31'),
(2, 1, 5, '삼성전자 AI 연구원 모집', 'MID_LEVEL', '2024-12-01', '2024-12-31'),
(3, 4, 1, '네이버 풀스택 개발자 채용', 'JUNIOR', '2024-12-15', '2025-01-15'),
(4, 5, 2, '카카오 모바일 앱 개발자 모집', 'ENTRY_LEVEL', '2024-12-10', '2025-01-10'),
(5, 6, 1, '토스 백엔드 개발자 채용', 'MID_LEVEL', '2024-12-20', '2025-01-20');

-- 샘플 회사-해시태그 연결
INSERT INTO summary_hashtags (company_id, hashtag_id) VALUES
(1, 1), (1, 2), (1, 4),  -- 삼성전자: 반도체, 전자제품, AI
(4, 4), (4, 9), (4, 8),  -- 네이버: AI, 플랫폼, 커머스
(5, 3), (5, 9), (5, 8),  -- 카카오: 모바일, 플랫폼, 커머스
(6, 7), (6, 9), (6, 10), -- 토스: 핀테크, 플랫폼, 스타트업
(8, 6), (8, 9);          -- 크래프톤: 게임, 플랫폼

-- 샘플 뉴스 데이터
INSERT INTO news (summary_hashtag_id, title, content, posting_date) VALUES
(1, '삼성전자, 차세대 반도체 기술 발표', '삼성전자가 3나노 공정 기술을 활용한 새로운 반도체 제품을 발표했습니다.', '2025-09-29'),
(2, '네이버, AI 기술 기반 새로운 서비스 론칭', '네이버가 생성형 AI를 활용한 새로운 검색 서비스를 출시한다고 발표했습니다.', '2025-09-29'),
(3, '카카오, 모바일 플랫폼 확장 계획 발표', '카카오가 글로벌 모바일 시장 진출을 위한 새로운 전략을 공개했습니다.', '2025-09-29'),
(4, '토스, 핀테크 업계 혁신 상품 출시', '토스가 새로운 투자 상품과 금융 서비스를 론칭했습니다.', '2025-09-29'),
(5, '크래프톤, 신작 게임 개발 소식', '크래프톤이 차세대 배틀로얄 게임 개발 현황을 공개했습니다.', '2025-09-29');

-- 샘플 회사 분석 요약 데이터
INSERT INTO company_analysis_summaries (company_id, business_overview, products_service, sales_contracts, rnd_activities, other_notes, status) VALUES
(1, '세계 최대 반도체 및 전자제품 제조업체로, 메모리 반도체, 시스템 반도체, 디스플레이, 모바일 기기 등을 생산합니다.',
    '갤럭시 스마트폰, DRAM, NAND 플래시, OLED 디스플레이, 가전제품 등',
    '글로벌 B2B 고객사와의 장기 공급 계약 체결, 안정적인 매출 기반 확보',
    '차세대 반도체 공정 기술, 6G 통신 기술, AI 반도체 연구개발 활발',
    '2024년 HBM 메모리 수요 급증으로 실적 개선 예상', 'FINISHED'),

(4, '대한민국 대표 인터넷 기업으로 검색, 커머스, 콘텐츠, 클라우드 등 다양한 디지털 서비스를 제공합니다.',
    '네이버 검색, 쇼핑, 웹툰, 클로바, 네이버 클라우드 플랫폼 등',
    '글로벌 콘텐츠 유통 계약, 클라우드 서비스 기업 고객 확대',
    '생성형 AI 하이퍼클로바X 개발, 자율주행 기술 연구',
    'AI 기술을 활용한 새로운 검색 경험 제공 예정', 'FINISHED');

-- ===================================================================
-- 5. Private 서버용 데이터베이스 스키마
-- ===================================================================

USE private_app;

-- 뉴스 처리 상태 추적 테이블
CREATE TABLE news_processing_status (
    id BIGINT NOT NULL AUTO_INCREMENT,
    news_url VARCHAR(1000) NOT NULL COMMENT '처리할 뉴스 URL',
    status ENUM('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED') NOT NULL DEFAULT 'PENDING' COMMENT '처리 상태',
    processed_at TIMESTAMP NULL COMMENT '처리 완료 시간',
    error_message TEXT COMMENT '오류 메시지',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_news_processing_url (news_url),
    INDEX idx_news_processing_status (status),
    INDEX idx_news_processing_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
COMMENT='뉴스 처리 상태 추적 테이블';

-- 크롤링 로그 테이블
CREATE TABLE crawling_logs (
    id BIGINT NOT NULL AUTO_INCREMENT,
    source VARCHAR(100) NOT NULL COMMENT '크롤링 소스 (naver, dart 등)',
    target_url VARCHAR(1000) COMMENT '크롤링 대상 URL',
    status ENUM('SUCCESS', 'FAILED') NOT NULL COMMENT '크롤링 결과',
    items_count INT DEFAULT 0 COMMENT '수집된 항목 수',
    error_message TEXT COMMENT '오류 메시지',
    execution_time_ms INT COMMENT '실행 시간 (밀리초)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_crawling_logs_source_status (source, status),
    INDEX idx_crawling_logs_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
COMMENT='크롤링 실행 로그 테이블';

-- 회사 매핑 상태 테이블
CREATE TABLE company_mapping_status (
    id BIGINT NOT NULL AUTO_INCREMENT,
    original_name VARCHAR(255) NOT NULL COMMENT '원본 회사명',
    mapped_company_id BIGINT COMMENT '매핑된 회사 ID',
    confidence_score INT DEFAULT 0 COMMENT '매핑 신뢰도 (0-100)',
    status ENUM('PENDING', 'MAPPED', 'MANUAL_REVIEW', 'REJECTED') NOT NULL DEFAULT 'PENDING' COMMENT '매핑 상태',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_company_mapping_original_name (original_name),
    INDEX idx_company_mapping_status (status),
    INDEX idx_company_mapping_confidence (confidence_score)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
COMMENT='회사명 매핑 상태 관리 테이블';

-- ===================================================================
-- 6. 성능 최적화 인덱스
-- ===================================================================

USE maindb;

-- 복합 인덱스 추가
CREATE INDEX idx_job_postings_company_sector_date ON job_postings(company_id, job_sector_id, posting_date);
CREATE INDEX idx_news_date_company ON news(posting_date, summary_hashtag_id);
CREATE INDEX idx_company_analysis_company_updated ON company_analysis_summaries(company_id, updated_at);

-- ===================================================================
-- 7. 사용자 권한 설정
-- ===================================================================

-- 애플리케이션용 사용자 생성 (실제 운영 시 비밀번호 변경 필요)
CREATE USER IF NOT EXISTS 'dart'@'%' IDENTIFIED BY 'your_mysql_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON maindb.* TO 'dart'@'%';

CREATE USER IF NOT EXISTS 'private_user'@'%' IDENTIFIED BY 'your_private_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON private_app.* TO 'private_user'@'%';

-- 권한 적용
FLUSH PRIVILEGES;

-- ===================================================================
-- 8. 데이터베이스 백업 및 복원 가이드
-- ===================================================================

/*
백업 명령어:
mysqldump -u root -p --single-transaction --routines --triggers maindb > maindb_backup_$(date +%Y%m%d_%H%M%S).sql
mysqldump -u root -p --single-transaction --routines --triggers private_app > private_app_backup_$(date +%Y%m%d_%H%M%S).sql

복원 명령어:
mysql -u root -p maindb < maindb_backup_20241229_120000.sql
mysql -u root -p private_app < private_app_backup_20241229_120000.sql

스키마만 백업 (데이터 제외):
mysqldump -u root -p --no-data maindb > maindb_schema_$(date +%Y%m%d_%H%M%S).sql
*/

-- ===================================================================
-- 9. 데이터베이스 상태 확인 쿼리
-- ===================================================================

/*
-- 테이블별 데이터 건수 확인
SELECT
    'users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'companies', COUNT(*) FROM companies
UNION ALL
SELECT 'job_postings', COUNT(*) FROM job_postings
UNION ALL
SELECT 'news', COUNT(*) FROM news
UNION ALL
SELECT 'company_analysis_summaries', COUNT(*) FROM company_analysis_summaries;

-- 인덱스 사용률 확인
SHOW INDEX FROM job_postings;
SHOW INDEX FROM news;
SHOW INDEX FROM companies;

-- 테이블 크기 확인
SELECT
    table_name,
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS table_size_mb
FROM information_schema.tables
WHERE table_schema = 'maindb'
ORDER BY table_size_mb DESC;
*/

-- ===================================================================
-- 완료
-- ===================================================================

-- 생성일: 2024-12-29
-- 버전: 1.0
-- 호환성: MySQL 8.0+
-- 인코딩: UTF-8

SELECT 'DABOJOB 데이터베이스 스키마 생성 완료!' as message;