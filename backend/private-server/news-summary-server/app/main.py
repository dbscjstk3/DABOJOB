import os
import sys
import logging
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import ollama

# 공통 모듈 import
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from common.redis_client import RedisStreamClient

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="news-summary-server")

# 환경변수 설정
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'localhost:11434')
MODEL_NAME = os.getenv('MODEL_NAME', 'qwen2.5:0.5b-instruct-fp16')

# 전역 클라이언트
ollama_client = None
redis_client = None

class NewsRequest(BaseModel):
    mapping_id: int
    summaries: Dict[int, str]  # {chapter: summary}
    keywords: List[str]

class NewsResponse(BaseModel):
    mapping_id: int
    news_summary: str
    keywords_used: List[str]
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
        
        logger.info("News-Summary server initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize server: {e}")
        raise

@app.get("/health")
def health_check() -> dict:
    return {
        "status": "ok",
        "service": "news-summary",
        "model": MODEL_NAME,
        "ollama_host": OLLAMA_HOST
    }

@app.post("/generate-news", response_model=NewsResponse)
async def generate_news_summary(request: NewsRequest) -> NewsResponse:
    """뉴스 형식 종합 요약 생성"""
    try:
        logger.info(f"Processing news generation: mapping_id={request.mapping_id}")
        
        # 챕터별 요약을 하나로 합치기
        all_summaries = "\n\n".join([
            f"【{chapter}장】 {summary}" 
            for chapter, summary in request.summaries.items()
        ])
        
        keywords_text = ", ".join(request.keywords)
        
        # 뉴스 형식 종합 요약 프롬프트
        news_prompt = f"""다음 DART 공시 챕터별 요약들을 바탕으로 뉴스 기사 형식의 종합 요약을 작성해주세요:

챕터별 요약:
{all_summaries}

핵심 키워드: {keywords_text}

뉴스 작성 요구사항:
1. 뉴스 기사 스타일로 작성 (제목 + 본문)
2. 제목은 "【속보】"로 시작
3. 핵심 키워드를 자연스럽게 본문에 포함
4. 중요한 수치, 날짜, 금액 등 구체적 정보 포함
5. 800자 내외로 작성
6. 객관적이고 간결한 문체
7. 투자자 관점에서 중요한 정보 위주

뉴스 기사:"""
        
        # Ollama API 호출 (0.5B 모델, FP16)
        response = ollama_client.chat(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": news_prompt}],
            options={
                "temperature": 0.3,
                "top_p": 0.9
            }
        )
        
        news_summary = response['message']['content'].strip()
        
        # 완료 알림 전송
        redis_client.send_complete(mapping_id=request.mapping_id)
        
        # 완료 카운터 증가
        completed_count = redis_client.increment_completion_counter(request.mapping_id)
        logger.info(f"Completion count for mapping_id={request.mapping_id}: {completed_count}")
        
        logger.info(f"News generation completed: mapping_id={request.mapping_id}")
        
        return NewsResponse(
            mapping_id=request.mapping_id,
            news_summary=news_summary,
            keywords_used=request.keywords
        )
        
    except Exception as e:
        logger.error(f"News generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-from-keywords")
async def generate_news_from_keywords(
    mapping_id: int,
    keywords: List[str]
) -> Dict[str, Any]:
    """키워드만으로 뉴스 생성 (단순 버전)"""
    try:
        logger.info(f"Generating news from keywords: mapping_id={mapping_id}, keywords={keywords}")
        
        keywords_text = ", ".join(keywords)
        
        simple_prompt = f"""다음 키워드들을 바탕으로 간단한 뉴스 요약을 작성해주세요:

키워드: {keywords_text}

요구사항:
1. 500자 내외
2. 뉴스 형식 (제목 + 본문)
3. 키워드를 자연스럽게 포함
4. 객관적인 문체

뉴스:"""
        
        response = ollama_client.chat(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": simple_prompt}],
            options={
                "temperature": 0.4,
                "top_p": 0.9
            }
        )
        
        news_text = response['message']['content'].strip()
        
        return {
            "mapping_id": mapping_id,
            "news_summary": news_text,
            "keywords": keywords,
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Simple news generation failed: {e}")
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
            "service": "news-summary",
            "status": "running",
            "model": MODEL_NAME,
            "model_type": "qwen2.5-0.5b-fp16",
            "ollama_host": OLLAMA_HOST,
            "ollama_status": ollama_status,
            "redis_info": redis_status
        }
    except Exception as e:
        return {
            "service": "news-summary",
            "status": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8200)
