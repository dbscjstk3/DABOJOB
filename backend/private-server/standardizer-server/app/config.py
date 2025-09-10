"""
공통 설정 관리
"""
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# Redis 설정
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))

# Redis Stream 설정
STREAM_SUMMARY = "stream:summary"
STREAM_NEWS = "stream:news"
STREAM_COMPLETE = "stream:complete"

# Consumer Group 설정
GROUP_SUMMARY = "summary-group"
GROUP_NEWS = "news-group"

# MySQL 설정 (나중에 사용)
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'dabojob')

# S3 설정 (나중에 사용)
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'ap-northeast-2')
S3_BUCKET = os.getenv('S3_BUCKET', 'dart-analysis-bucket')

# 파일 시스템 설정
DATA_ROOT = "/app/data/mappings"

# 고정 값
TOTAL_CHAPTERS = 5
KEYWORDS_PER_CHAPTER = 3