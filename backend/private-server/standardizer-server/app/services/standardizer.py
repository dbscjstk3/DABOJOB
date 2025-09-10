import logging
import os
from typing import Optional
import ollama

logger = logging.getLogger(__name__)

class StandardizerService:
    def __init__(self, ollama_host: Optional[str] = None, model_name: Optional[str] = None):
        """
        표준화 서비스 초기화
        
        Args:
            ollama_host (str): Ollama 서버 호스트
            model_name (str): 사용할 모델명
        """
        self.ollama_host = ollama_host or os.getenv('OLLAMA_HOST', 'ollama:11434')
        self.model_name = model_name or os.getenv('STANDARDIZER_MODEL', 'qwen2.5:0.5b-instruct-fp16')
        self.client = None
        
    async def initialize(self):
        """Ollama 클라이언트 초기화"""
        try:
            host = self.ollama_host if self.ollama_host.startswith('http') else f'http://{self.ollama_host}'
            self.client = ollama.Client(host=host)
            
            # 연결 테스트
            models = self.client.list()
            logger.info(f"Connected to Ollama at {host}")
            logger.info(f"Available models: {[m['name'] for m in models['models']]}")
            logger.info(f"Using model: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Ollama client: {e}")
            raise
    
    async def standardize_text(self, content: str) -> str:
        """
        텍스트 표준화 처리
        
        Args:
            content (str): 표준화할 텍스트
            
        Returns:
            str: 표준화된 텍스트
        """
        if not self.client:
            raise RuntimeError("Standardizer service not initialized")
        
        try:
            # 표준화 프롬프트
            prompt = f"""다음 텍스트를 표준화해주세요:

원본 텍스트:
{content}

표준화 요구사항:
1. 불필요한 공백 정리
2. 특수문자 정규화
3. 일관된 표기법 사용

표준화된 텍스트만 출력:"""
            
            # Ollama API 호출
            response = self.client.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                options={
                    "temperature": 0.1,
                    "top_p": 0.9
                }
            )
            
            return response['message']['content'].strip()
            
        except Exception as e:
            logger.error(f"Text standardization failed: {e}")
            raise
    
    def get_status(self) -> dict:
        """서비스 상태 반환"""
        return {
            "ollama_host": self.ollama_host,
            "model_name": self.model_name,
            "initialized": self.client is not None
        }