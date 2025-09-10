import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import ollama

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="standardizer-server")

# 환경변수에서 올바른 이름으로 가져오기
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'ollama:11434')
MODEL_NAME = os.getenv('STANDARDIZER_MODEL', 'qwen2.5:0.5b-instruct-fp16')

# Ollama 클라이언트
ollama_client = None

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
    global ollama_client
    
    try:
        host = OLLAMA_HOST if OLLAMA_HOST.startswith('http') else f'http://{OLLAMA_HOST}'
        ollama_client = ollama.Client(host=host)
        
        # 연결 테스트
        models = ollama_client.list()
        logger.info(f"Connected to Ollama at {host}")
        logger.info(f"Available models: {[m['name'] for m in models['models']]}")
        logger.info(f"Using model: {MODEL_NAME}")
        
    except Exception as e:
        logger.error(f"Failed to initialize Ollama client: {e}")
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
        
        # 표준화 프롬프트
        prompt = f"""다음 텍스트를 표준화해주세요:

원본 텍스트:
{request.content}

표준화 요구사항:
1. 불필요한 공백 정리
2. 특수문자 정규화
3. 일관된 표기법 사용

표준화된 텍스트만 출력:"""
        
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
        
        logger.info(f"Standardization completed: mapping_id={request.mapping_id}")
        
        return StandardizeResponse(
            mapping_id=request.mapping_id,
            chapter=request.chapter,
            standardized_content=standardized_content
        )
        
    except Exception as e:
        logger.error(f"Standardization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)