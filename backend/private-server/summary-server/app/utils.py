import re
import logging
from typing import Optional, List

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

# 메타 표현 제거 패턴
META_PATTERNS = [
    r'.*?텍스트입니다\.?\s*',
    r'.*?내용입니다\.?\s*', 
    r'.*?문서입니다\.?\s*',
    r'.*?보고서입니다\.?\s*',
    r'다음은.*?요약입니다\.?\s*',
    r'이.*?요약.*?입니다\.?\s*',
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

def remove_meta_expressions(text: str) -> str:
    """메타 표현 제거"""
    cleaned = text
    
    for pattern in META_PATTERNS:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # "..." 으로 끝나는 경우 완전한 문장으로 마무리
    if cleaned.endswith('...'):
        # 마지막 완전한 문장 찾기
        sentences = re.split(r'[.!?]\s+', cleaned[:-3])
        if len(sentences) > 1:
            cleaned = '. '.join(sentences[:-1]) + '.'
    
    return cleaned.strip()

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

def split_text_with_sliding_window(text: str, chunk_size: int = 1200, overlap: int = 100) -> List[str]:
    """겹치는 윈도우 방식으로 텍스트 분할"""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        # 청크 끝 위치 계산
        end = start + chunk_size
        
        if end >= len(text):
            # 마지막 청크
            chunks.append(text[start:])
            break
        
        # 문장 경계에서 자르기 위해 조정
        chunk_text = text[start:end]
        
        # 마지막 완전한 문장 찾기
        last_sentence_end = max(
            chunk_text.rfind('.'),
            chunk_text.rfind('!'),
            chunk_text.rfind('?')
        )
        
        if last_sentence_end > chunk_size * 0.7:  # 최소 70% 이상의 내용 확보
            end = start + last_sentence_end + 1
        
        chunks.append(text[start:end].strip())
        
        # 다음 청크 시작점 (겹치는 부분 고려)
        start = end - overlap
        if start < 0:
            start = 0
    
    return chunks

@measure_performance("1단계: 청크별 요약")
def _summarize_chunk(ollama_client, model_name: str, text: str, target_length: int) -> str:
    """단일 텍스트 청크 요약 (1단계)"""
    prompt = f"""다음 텍스트의 핵심 내용을 {target_length}자 내외로 요약하세요.

중요 지침:
1. 구체적인 사실, 수치, 날짜, 회사명 포함
2. "텍스트입니다", "내용입니다" 같은 메타 표현 금지
3. 완전한 문장으로 끝내기
4. 사진/이미지 관련 내용 제외
5. 객관적 사실만 나열

텍스트:
{text}

핵심 요약:"""
    
    try:
        response = ollama_client.chat(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": 0.1,
                "top_p": 0.8,
                "max_tokens": target_length // 2
            }
        )
        
        summary = response['message']['content'].strip()
        return remove_meta_expressions(summary)
        
    except Exception as e:
        logger.error(f"청크 요약 실패: {e}")
        return text[:target_length] if len(text) > target_length else text

@measure_performance("2단계: 통합 요약")
def _integrate_summaries(ollama_client, model_name: str, summaries: List[str], max_length: int) -> str:
    """청크 요약들을 통합하여 최종 요약 생성 (2단계)"""
    combined_text = " ".join(summaries)
    
    prompt = f"""다음 여러 요약문들을 하나의 완성된 요약으로 통합하세요.

중요 지침:
1. {max_length}자 이내로 작성
2. 중복된 내용 제거하고 논리적 순서로 재구성
3. 구체적 수치와 사실 중심으로 작성
4. "요약입니다", "텍스트입니다" 같은 메타 표현 절대 금지
5. 완전한 문장으로 끝내기
6. 자연스러운 하나의 문단으로 작성

개별 요약들:
{combined_text}

통합 요약:"""
    
    try:
        response = ollama_client.chat(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": 0.2,
                "top_p": 0.9,
                "max_tokens": max_length // 2
            }
        )
        
        summary = response['message']['content'].strip()
        final_summary = remove_meta_expressions(summary)
        
        # 길이 제한 확인
        if len(final_summary) > max_length:
            # 마지막 완전한 문장에서 자르기
            sentences = re.split(r'[.!?]\s+', final_summary)
            result = ""
            for sentence in sentences:
                if len(result + sentence + ".") <= max_length:
                    result += sentence + ". "
                else:
                    break
            final_summary = result.strip()
        
        return final_summary
        
    except Exception as e:
        logger.error(f"통합 요약 실패: {e}")
        return combined_text[:max_length] if len(combined_text) > max_length else combined_text

@measure_performance("전체 AI 모델 요약")
def qwen_summarize_long(ollama_client, model_name: str, text: str, max_length: int = 500) -> str:
    """개선된 2단계 요약 (슬라이딩 윈도우 + 통합 요약)"""
    # 텍스트 전처리
    cleaned_text = clean_text(text)
    
    # 짧은 텍스트는 바로 요약
    if len(cleaned_text) <= 1500:
        return _summarize_chunk(ollama_client, model_name, cleaned_text, max_length)
    
    # 긴 텍스트는 2단계 처리
    logger.info(f"긴 텍스트 감지: {len(cleaned_text)}자 → 2단계 요약 시작")
    
    # 1단계: 겹치는 윈도우로 청크 분할 및 개별 요약
    chunks = split_text_with_sliding_window(cleaned_text, chunk_size=1200, overlap=100)
    logger.info(f"총 {len(chunks)}개 청크로 분할")
    
    chunk_summaries = []
    for i, chunk in enumerate(chunks):
        target_length = max_length // len(chunks) + 100  # 여유분 추가
        chunk_summary = _summarize_chunk(ollama_client, model_name, chunk, target_length)
        chunk_summaries.append(chunk_summary)
        logger.info(f"청크 {i+1}/{len(chunks)} 요약 완료: {len(chunk_summary)}자")
    
    # 2단계: 청크 요약들을 통합하여 최종 요약
    final_summary = _integrate_summaries(ollama_client, model_name, chunk_summaries, max_length)
    
    logger.info(f"최종 요약 완료: {len(final_summary)}자")
    return final_summary