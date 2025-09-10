import os
import sys
import logging
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import ollama

# Redis 모듈 import (같은 디렉토리에서)
from redis_client import RedisStreamClient

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="summary-server")

# 환경변수 설정
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'localhost:11434')
MODEL_NAME = os.getenv('MODEL_NAME', 'qwen2.5:1.8b-instruct-q4_0')

# 전역 클라이언트
ollama_client = None
redis_client = None

class SummarizeRequest(BaseModel):
    mapping_id: int
    chapter: int
    content: str
    max_length: int = 500

class SummarizeResponse(BaseModel):
    mapping_id: int
    chapter: int
    summary: str
    keywords: List[str]
    status: str = "completed"

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 초기화"""
    global ollama_client, redis_client
    
    try:
        # Ollama 클라이언트 초기화
        host = OLLAMA_HOST if OLLAMA_HOST.startswith('http') else f'http://{OLLAMA_HOST}'
        ollama_client = ollama.Client(host=host)
        
        # 연결 테스트
        models = ollama_client.list()
        logger.info(f"Connected to Ollama at {host}")
        logger.info(f"Available models: {[m['name'] for m in models['models']]}")
        
        # Redis 클라이언트 초기화
        redis_client = RedisStreamClient()
        redis_client.setup_consumer_groups()
        
        logger.info("Summary server initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize server: {e}")
        raise

@app.get("/health")
def health_check() -> dict:
    return {
        "status": "ok",
        "service": "summary", 
        "model": MODEL_NAME,
        "ollama_host": OLLAMA_HOST
    }

@app.post("/summarize", response_model=SummarizeResponse)
async def summarize_content(request: SummarizeRequest) -> SummarizeResponse:
    """텍스트 요약 처리"""
    try:
        logger.info(f"Processing summarization: mapping_id={request.mapping_id}, chapter={request.chapter}")
        
        # 요약 전용 프롬프트
        summary_prompt = f"""다음 DART 공시 텍스트를 {request.max_length}자 이내로 요약해주세요:

텍스트:
{request.content}

요약 요구사항:
1. 핵심 내용 위주로 요약
2. 중요한 수치, 날짜, 금액 포함
3. 명확하고 간결한 문체
4. {request.max_length}자 이내로 작성
5. 객관적이고 정확한 정보 전달

요약문만 출력하세요:"""
        
        # 요약 생성
        summary_response = ollama_client.chat(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": summary_prompt}],
            options={
                "temperature": 0.2,
                "top_p": 0.9
            }
        )
        
        summary = summary_response['message']['content'].strip()
        
        # 키워드 추출 프롬프트
        keyword_prompt = f"""다음 텍스트에서 핵심 키워드 3개를 추출해주세요:

텍스트:
{request.content}

요구사항:
1. 가장 중요한 키워드 3개
2. 명사 위주로 선택
3. 콤마(,)로 구분하여 출력
4. 키워드만 출력 (설명 없이)

키워드:"""
        
        # 키워드 추출
        keyword_response = ollama_client.chat(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": keyword_prompt}],
            options={
                "temperature": 0.3,
                "top_p": 0.9
            }
        )
        
        keywords_text = keyword_response['message']['content'].strip()
        keywords = [k.strip() for k in keywords_text.split(',')][:3]
        
        # Redis로 다음 단계(News) 전송
        if len(keywords) == 3:
            redis_client.send_to_news(
                mapping_id=request.mapping_id,
                chapter=request.chapter,
                keywords=keywords
            )
        else:
            logger.warning(f"Expected 3 keywords, got {len(keywords)}: {keywords}")
        
        logger.info(f"Summarization completed: mapping_id={request.mapping_id}, chapter={request.chapter}")
        
        return SummarizeResponse(
            mapping_id=request.mapping_id,
            chapter=request.chapter,
            summary=summary,
            keywords=keywords
        )
        
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
def get_status() -> Dict[str, Any]:
    """서버 상태 조회"""
    try:
        # Ollama 연결 테스트
        ollama_status = "connected"
        try:
            ollama_client.list()
        except:
            ollama_status = "disconnected"
            
        # Redis 상태
        redis_status = {}
        if redis_client:
            redis_status = redis_client.get_stream_info()
        
        return {
            "service": "summary",
            "status": "running", 
            "model": MODEL_NAME,
            "ollama_host": OLLAMA_HOST,
            "ollama_status": ollama_status,
            "redis_info": redis_status
        }
    except Exception as e:
        return {
            "service": "summary",
            "status": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8100)
