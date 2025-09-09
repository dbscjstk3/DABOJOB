from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
import logging
from .models.vllm_client import VLLMClient

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 전역 모델 인스턴스
vllm_client = VLLMClient()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 라이프사이클 관리"""
    # 시작 시 모델 로드
    logger.info("Starting Summary Server...")
    success = vllm_client.initialize()
    if not success:
        logger.error("Failed to initialize vLLM model")
    else:
        logger.info("vLLM model initialized successfully")
    
    yield
    
    # 종료 시 정리
    logger.info("Shutting down Summary Server...")

app = FastAPI(
    title="summary-server",
    description="AI Summary Service with vLLM + Qwen2",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
def health_check() -> dict:
    """헬스 체크 엔드포인트"""
    model_info = {
        "status": "ok",
        "model_initialized": vllm_client.is_initialized(),
        "model_name": vllm_client.model_name
    }
    return model_info

@app.get("/model/info")
def get_model_info() -> dict:
    """모델 정보 조회"""
    if not vllm_client.is_initialized():
        raise HTTPException(status_code=503, detail="Model not initialized")
    
    import torch
    return {
        "model_name": vllm_client.model_name,
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "cuda_available": torch.cuda.is_available(),
        "initialized": True
    }
