import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# 불필요한 패턴들 (사진, 이미지 관련)
USELESS_PATTERNS = [
    r'\[사진\].*?\[/사진\]',
    r'\[이미지\].*?\[/이미지\]', 
    r'\[그림\].*?\[/그림\]',
    r'사진=.*?(?=\s|$)',
    r'이미지=.*?(?=\s|$)',
    r'\(사진.*?\)',
    r'\(이미지.*?\)',
    r'사진\s*제공[:=].*?(?=\s|$)',
    r'이미지\s*제공[:=].*?(?=\s|$)',
    r'\[.*?사진.*?\]',
    r'\[.*?이미지.*?\]',
    r'연합뉴스.*?제공',
    r'뉴시스.*?제공',
    r'게티이미지.*?제공'
]

def clean_text(text: str) -> str:
    """사진/이미지 관련 정보와 불필요한 패턴 제거"""
    cleaned = text
    
    # 불필요한 패턴들 제거
    for pattern in USELESS_PATTERNS:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # 연속된 공백 정리
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # 앞뒤 공백 제거
    cleaned = cleaned.strip()
    
    return cleaned

def measure_performance(description: str):
    """성능 측정 데코레이터"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            logger.info(f"{description}: {end_time - start_time:.2f}초")
            return result
        return wrapper
    return decorator

@measure_performance("AI 모델 추론")
def qwen_summarize(ollama_client, model_name: str, text: str, target_sentences: int = 2) -> str:
    """개선된 Qwen 모델 요약 (메모리 모니터링 포함)"""
    # 텍스트 전처리
    cleaned_text = clean_text(text)
    
    prompt = f"""다음 뉴스 기사를 정확히 {target_sentences}개의 완전한 한국어 문장으로 요약하세요.

필수 조건:
1. 반드시 100자 이내로 작성
2. 핵심 내용만 포함
3. 완전한 한국어 문장으로만 응답
4. 중국어, 영어 등 다른 언어 사용 금지
5. 사진이나 이미지 관련 내용은 제외
6. "..." 같은 생략 표시 없이 완성된 문장

기사 내용:
{cleaned_text}

한국어 100자 요약:"""
    
    try:
        response = ollama_client.chat(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": 0.1,
                "top_p": 0.9,
                "num_predict": 150  # Ollama에서는 max_tokens 대신 num_predict 사용
            }
        )
        
        summary = response['message']['content'].strip()
        
        # 후처리: 100자 제한 확인
        if len(summary) > 100:
            summary = summary[:97] + "..."
            
        return summary
        
    except Exception as e:
        logger.error(f"Qwen summarization failed: {e}")
        raise