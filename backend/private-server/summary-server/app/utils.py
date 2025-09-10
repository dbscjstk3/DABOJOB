import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# 불필요한 패턴들 (사진, 이미지, 표, 차트 관련)
USELESS_PATTERNS = [
    r'\[사진\].*?\[/사진\]',
    r'\[이미지\].*?\[/이미지\]', 
    r'\[그림\].*?\[/그림\]',
    r'\[표\].*?\[/표\]',
    r'\[차트\].*?\[/차트\]',
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
    r'게티이미지.*?제공',
    r'<.*?>',  # HTML 태그 제거
    r'\s*\n\s*\n\s*',  # 여러 줄바꿈 정리
]

def clean_text(text: str) -> str:
    """사진/이미지/표 관련 정보와 불필요한 패턴 제거"""
    cleaned = text
    
    # 불필요한 패턴들 제거
    for pattern in USELESS_PATTERNS:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # 연속된 공백과 줄바꿈 정리
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = re.sub(r'\n+', '\n', cleaned)
    
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

@measure_performance("AI 모델 요약")
def qwen_summarize_long(ollama_client, model_name: str, text: str, max_length: int = 500) -> str:
    """개선된 Qwen 모델 긴 텍스트 요약"""
    # 텍스트 전처리
    cleaned_text = clean_text(text)
    
    # 텍스트가 너무 길면 청크로 나누기
    if len(cleaned_text) > 2000:
        chunks = split_text_into_chunks(cleaned_text, 1500)
        summaries = []
        
        for i, chunk in enumerate(chunks):
            chunk_summary = _summarize_chunk(ollama_client, model_name, chunk, max_length // len(chunks))
            summaries.append(chunk_summary)
            logger.info(f"청크 {i+1}/{len(chunks)} 요약 완료")
        
        # 청크 요약들을 다시 종합 요약
        combined_text = " ".join(summaries)
        if len(combined_text) > max_length:
            return _summarize_chunk(ollama_client, model_name, combined_text, max_length)
        return combined_text
    
    else:
        return _summarize_chunk(ollama_client, model_name, cleaned_text, max_length)

def split_text_into_chunks(text: str, chunk_size: int = 1500) -> list:
    """텍스트를 의미있는 단위로 청크 분할"""
    # 문장 단위로 분할
    sentences = re.split(r'[.!?]\s+', text)
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk + sentence) < chunk_size:
            current_chunk += sentence + ". "
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + ". "
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def _summarize_chunk(ollama_client, model_name: str, text: str, max_length: int) -> str:
    """단일 텍스트 청크 요약"""
    prompt = f"""다음 텍스트를 핵심 내용 중심으로 요약하세요.

조건:
1. {max_length}자 이내로 작성
2. 핵심 정보와 수치만 포함
3. 명확하고 간결한 문장 사용
4. 사진, 이미지, 표 관련 내용은 제외
5. 완전한 한국어 문장으로 작성

원본 텍스트:
{text}

요약:"""
    
    try:
        response = ollama_client.chat(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": 0.2,
                "top_p": 0.9,
                "max_tokens": max_length // 2  # 한글 특성상 토큰 수 조정
            }
        )
        
        summary = response['message']['content'].strip()
        
        # 후처리: 길이 제한 확인
        if len(summary) > max_length:
            summary = summary[:max_length-3] + "..."
            
        return summary
        
    except Exception as e:
        logger.error(f"청크 요약 실패: {e}")
        # 요약 실패 시 원본 텍스트 잘라서 반환
        return text[:max_length-3] + "..." if len(text) > max_length else text