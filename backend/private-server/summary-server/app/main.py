import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import ollama

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="summary-server")

# 환경변수에서 올바른 이름으로 가져오기
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'ollama:11434')
MODEL_NAME = os.getenv('SUMMARY_MODEL', 'qwen2.5:0.5b-instruct-fp16')

# Ollama 클라이언트
ollama_client = None

class SummarizeRequest(BaseModel):
    mapping_id: int
    chapter: int
    content: str
    file_path: str = ""
    max_length: int = 500

class SummarizeResponse(BaseModel):
    mapping_id: int
    chapter: int
    summary: str
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
        "service": "summary",
        "model": MODEL_NAME,
        "ollama_host": OLLAMA_HOST
    }

@app.post("/summarize", response_model=SummarizeResponse)
async def summarize_content(request: SummarizeRequest) -> SummarizeResponse:
    """텍스트 요약 처리"""
    try:
        logger.info(f"Processing summary: mapping_id={request.mapping_id}, chapter={request.chapter}")
        
        # 요약 프롬프트
        prompt = f"""다음 텍스트를 핵심 내용 중심으로 요약해주세요:

원본 텍스트:
{request.content}

요약 요구사항:
1. 핵심 정보만 포함
2. {request.max_length}자 이내로 작성
3. 명확하고 간결한 문장 사용

요약문:"""
        
        # Ollama API 호출
        response = ollama_client.chat(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": 0.3,
                "top_p": 0.9
            }
        )
        
        summary = response['message']['content'].strip()
        
        logger.info(f"Summary completed: mapping_id={request.mapping_id}")
        
        return SummarizeResponse(
            mapping_id=request.mapping_id,
            chapter=request.chapter,
            summary=summary
        )
        
    except Exception as e:
        logger.error(f"Summary failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8100)