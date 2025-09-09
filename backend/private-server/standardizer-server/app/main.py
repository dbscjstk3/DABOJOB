import os
import sys
import logging
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import ollama

# 공통 모듈 import
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from common.redis_client import RedisStreamClient

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="standardizer-server")

# 환경변수 설정
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'localhost:11434')
MODEL_NAME = os.getenv('MODEL_NAME', 'qwen2.5:1.8b-instruct-q4_0')

# 전역 클라이언트
ollama_client = None
redis_client = None

class StandardizeRequest(BaseModel):
    mapping_id: int
    chapter: int
    content: str
    file_path: str = ""

class StandardizeResponse(BaseModel):
    mapping_id: int
    chapter: int
    standardized_content: str
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
        
        logger.info("Standardizer server initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize server: {e}")
        raise

@app.get("/health")
def health_check() -> dict:
    return {
        "status": "ok", 
        "service": "standardizer",
        "model": MODEL_NAME,
        "ollama_host": OLLAMA_HOST
    }

@app.post("/standardize", response_model=StandardizeResponse)
async def standardize_content(request: StandardizeRequest) -> StandardizeResponse:
    """텍스트 표준화 처리"""
    try:
        logger.info(f"Processing standardization: mapping_id={request.mapping_id}, chapter={request.chapter}")
        
        # 표준화 전용 프롬프트
        prompt = f"""다음 DART 공시 텍스트를 표준화해주세요:

원본 텍스트:
{request.content}

표준화 요구사항:
1. 불필요한 공백과 줄바꿈 정리
2. 특수문자 정규화 (전각→반각)
3. 숫자 표기법 통일
4. 문장 구조 개선
5. 맞춤법 및 오타 수정
6. 일관된 용어 사용

표준화된 텍스트만 출력하세요:"""
        
        # Ollama API 호출
        response = ollama_client.chat(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": 0.1,
                "top_p": 0.9
            }
        )
        
        standardized_content = response['message']['content'].strip()
        
        # Redis로 다음 단계(Summary) 전송
        file_path = request.file_path or f"standardized_{request.mapping_id}_{request.chapter}.txt"
        redis_client.send_to_summary(
            mapping_id=request.mapping_id,
            chapter=request.chapter, 
            file_path=file_path
        )
        
        logger.info(f"Standardization completed: mapping_id={request.mapping_id}, chapter={request.chapter}")
        
        return StandardizeResponse(
            mapping_id=request.mapping_id,
            chapter=request.chapter,
            standardized_content=standardized_content
        )
        
    except Exception as e:
        logger.error(f"Standardization failed: {e}")
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
            "service": "standardizer",
            "status": "running",
            "model": MODEL_NAME,
            "ollama_host": OLLAMA_HOST,
            "ollama_status": ollama_status,
            "redis_info": redis_status
        }
    except Exception as e:
        return {
            "service": "standardizer", 
            "status": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
