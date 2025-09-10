import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import ollama

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="news-summary-server")

# 환경변수에서 올바른 이름으로 가져오기
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'ollama:11434')
MODEL_NAME = os.getenv('NEWS_MODEL', 'qwen2.5:0.5b-instruct-fp16')

# Ollama 클라이언트
ollama_client = None

class NewsSummarizeRequest(BaseModel):
    mapping_id: int
    chapter: int
    summary: str
    file_path: str = ""

class NewsSummarizeResponse(BaseModel):
    mapping_id: int
    chapter: int
    news_summary: str
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
        "service": "news-summary",
        "model": MODEL_NAME,
        "ollama_host": OLLAMA_HOST
    }

@app.post("/news-summarize", response_model=NewsSummarizeResponse)
async def news_summarize_content(request: NewsSummarizeRequest) -> NewsSummarizeResponse:
    """뉴스 스타일 요약 처리"""
    try:
        logger.info(f"Processing news summary: mapping_id={request.mapping_id}, chapter={request.chapter}")
        
        # 뉴스 스타일 요약 프롬프트
        prompt = f"""다음 요약문을 뉴스 헤드라인 스타일로 재작성해주세요:

원본 요약:
{request.summary}

뉴스 스타일 요구사항:
1. 간결하고 임팩트 있는 표현
2. 핵심 수치와 사실 중심
3. 객관적이고 중립적인 톤
4. 2문장으로 압축

뉴스 헤드라인:"""
        
        # Ollama API 호출
        response = ollama_client.chat(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": 0.5,
                "top_p": 0.9
            }
        )
        
        news_summary = response['message']['content'].strip()
        
        logger.info(f"News summary completed: mapping_id={request.mapping_id}")
        
        return NewsSummarizeResponse(
            mapping_id=request.mapping_id,
            chapter=request.chapter,
            news_summary=news_summary
        )
        
    except Exception as e:
        logger.error(f"News summary failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8200)