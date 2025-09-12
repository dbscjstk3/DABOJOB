import re
import logging
import asyncio
import os
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor

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

# 메타 표현 제거 패턴 (강화)
META_PATTERNS = [
    r'.*?텍스트입니다\.?\s*',
    r'.*?내용입니다\.?\s*', 
    r'.*?문서입니다\.?\s*',
    r'.*?보고서입니다\.?\s*',
    r'다음은.*?요약입니다\.?\s*',
    r'이.*?요약.*?입니다\.?\s*',
    r'이\s*텍스트는.*?',         # "이 텍스트는~" 제거
    r'해당\s*내용은.*?',         # "해당 내용은~" 제거
    r'.*?를\s*설명하고\s*',     # "~를 설명하고" 제거
    r'.*?를\s*나타내며\s*',     # "~를 나타내며" 제거
    r'.*?를\s*보여줍니다\s*',   # "~를 보여줍니다" 제거
    r'특히\s*',                  # "특히" 제거
    r'또한\s*',                  # "또한" 제거
    r'\*\*요약.*?\*\*\s*',      # **요약** 제거
    r'\*\*.*?\*\*\s*',          # 기타 **텍스트** 제거
    r'요약\s*[:：]\s*',          # "요약:" 제거
    r'^요약입니다\s*',            # 문장 시작의 "요약입니다" 제거
    r'\\n+',                    # \n 제거 (백슬래시 포함)
    r'\n+',                     # 실제 줄바꿈 제거
    r'\s*-\s*\*\*.*?\*\*\s*',   # - **제목** 형태 제거
    r'\d+\.\s*-\s*',            # "1. - " 형태 제거
    r'^\s*-\s*',                # 문장 시작의 "- " 제거
    r'\s*:\s*$',                # 문장 끝의 ":" 제거
    r'\d+\.\s*:\s*',           # "1. :" 형태 제거
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
    """성능 측정 데코레이터 (async/sync 모두 지원)"""
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                import time
                start_time = time.time()
                result = await func(*args, **kwargs)
                end_time = time.time()
                logger.info(f"{description}: {end_time - start_time:.2f}초")
                return result
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                import time
                start_time = time.time()
                result = func(*args, **kwargs)
                end_time = time.time()
                logger.info(f"{description}: {end_time - start_time:.2f}초")
                return result
            return sync_wrapper
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

def _ollama_call_sync(ollama_client, model_name: str, prompt: str, temperature: float, top_p: float, num_predict: int) -> str:
    """Ollama API 동기 호출 (executor에서 실행용)"""
    response = ollama_client.chat(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        options={
            "temperature": temperature,
            "top_p": top_p,
            "num_predict": num_predict  # Ollama에서는 max_tokens 대신 num_predict 사용
        }
    )
    return response['message']['content'].strip()

@measure_performance("1단계: 청크별 요약")
async def _summarize_chunk(ollama_client, model_name: str, text: str, target_length: int, executor: ThreadPoolExecutor = None) -> str:
    """단일 텍스트 청크 요약 (1단계)"""
    prompt = f"""다음 DART 공시자료의 핵심 내용을 {target_length}자로 정리하세요.

요약 원칙:
1. 회사가 어떤 사업을 하는지, 무엇을 만드는지 명확하게 설명
2. 사업의 특징과 경쟁력이 무엇인지 파악 가능하도록 서술
3. 주요 제품/서비스가 시장에서 어떤 위치인지 설명
4. 구체적 수치보다는 전반적인 흐름과 맥락 중심으로 정리
5. "~입니다", "~보여줍니다" 등 불필요한 서술 표현 제거
6. 자연스러운 문장으로 연결하여 읽기 쉽게 구성
7. 완전한 한국어 문장으로만 응답
8. 중국어, 영어 등 다른 언어 사용 금지

원문:
{text}"""
    
    try:
        if executor:
            loop = asyncio.get_event_loop()
            summary = await loop.run_in_executor(
                executor,
                _ollama_call_sync,
                ollama_client,
                model_name,
                prompt,
                0.1,
                0.8,
                target_length // 2
            )
        else:
            summary = _ollama_call_sync(
                ollama_client,
                model_name,
                prompt,
                0.1,
                0.8,
                target_length // 2
            )
        
        return remove_meta_expressions(summary)
        
    except Exception as e:
        logger.error(f"청크 요약 실패: {e}")
        return text[:target_length] if len(text) > target_length else text

@measure_performance("2단계: 통합 요약")
async def _integrate_summaries(ollama_client, model_name: str, summaries: List[str], max_length: int, category: str = None, executor: ThreadPoolExecutor = None) -> str:
    """청크 요약들을 통합하여 취준생 맞춤 최종 요약 생성"""
    combined_text = " ".join(summaries)
    
    # 카테고리별 맞춤 프롬프트 설정
    category_contexts = {
        "business_overview": "회사의 주력 사업분야와 각 사업부문이 어떻게 구성되어 있는지, 글로벌 시장에서 어떤 위치를 차지하는지",
        "products_services": "회사가 생산하는 주요 제품과 서비스는 무엇이며, 각각이 시장에서 어떤 경쟁력을 가지고 있는지",
        "revenue_orders": "회사의 매출 구조와 주요 고객사는 누구이며, 어떤 분야에서 수익을 창출하고 있는지",
        "contracts_rnd": "회사가 집중하는 연구개발 분야와 기술 혁신 방향, 주요 기술 제휴나 특허는 무엇인지",
        "other_references": "회사의 리스크 관리 체계와 지속가능경영 방향, 주요 투자나 인수합병 현황은 어떠한지"
    }
    
    context = category_contexts.get(category, "회사의 핵심 사업 내용과 특징")
    
    prompt = f"""다음 DART 공시자료를 {max_length}자로 요약하세요.

【요약 관점】
{context}를 중심으로 정리

【작성 지침】
• 회사가 무엇을 하는 회사인지 명확하게 이해할 수 있도록 서술
• 단순 나열이 아닌 문맥이 있는 설명으로 구성
• "이 회사는", "본 보고서는" 같은 메타 표현 제거
• 핵심 사업내용과 특징을 자연스럽게 연결하여 서술
• 불필요한 세부 수치보다는 전체적인 사업 구조와 특징 중심
• 완전한 한국어 문장으로만 응답
• 중국어, 영어 등 다른 언어 사용 금지

【원문】
{combined_text}

【요약】"""
    
    try:
        if executor:
            loop = asyncio.get_event_loop()
            summary = await loop.run_in_executor(
                executor,
                _ollama_call_sync,
                ollama_client,
                model_name,
                prompt,
                0.2,
                0.9,
1200
            )
        else:
            summary = _ollama_call_sync(
                ollama_client,
                model_name,
                prompt,
                0.2,
                0.9,
1200
            )
        
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
async def qwen_summarize_long(ollama_client, model_name: str, text: str, max_length: int = 500, category: str = None) -> str:
    """개선된 2단계 요약 (슬라이딩 윈도우 + 통합 요약)"""
    # Executor 생성 (동시 작업 제한)
    max_workers = int(os.getenv('MAX_WORKERS', '2'))
    executor = ThreadPoolExecutor(max_workers=max_workers)
    
    try:
        # 텍스트 전처리
        cleaned_text = clean_text(text)
        
        # 짧은 텍스트는 바로 요약 (1단계만)
        if len(cleaned_text) <= 1500:
            logger.info(f"짧은 텍스트: {len(cleaned_text)}자 → 1단계 직접 요약")
            return await _summarize_chunk(ollama_client, model_name, cleaned_text, max_length, executor)
    
        # 긴 텍스트는 청크 분할 확인
        chunks = split_text_with_sliding_window(cleaned_text, chunk_size=4000, overlap=400)
        logger.info(f"텍스트 분할: {len(cleaned_text)}자 → {len(chunks)}개 청크")
        
        # 청크가 1개면 1단계만 수행
        if len(chunks) == 1:
            logger.info("청크 1개 → 1단계 직접 요약")
            return await _summarize_chunk(ollama_client, model_name, chunks[0], max_length, executor)
        
        # 청크가 여러 개일 때만 2단계 처리
        logger.info(f"청크 {len(chunks)}개 → 2단계 요약 시작")
        
        # 동시성 제한을 위한 세마포어
        semaphore = asyncio.Semaphore(max_workers)
        
        async def process_chunk_with_limit(chunk, target_length):
            async with semaphore:
                result = await _summarize_chunk(ollama_client, model_name, chunk, target_length, executor)
                await asyncio.sleep(0.05)  # CPU 부하 분산
                return result
        
        # 1단계: 병렬로 청크 처리
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            target_length = max_length // len(chunks) + 100  # 여유분 추가
            chunk_summary = await process_chunk_with_limit(chunk, target_length)
            chunk_summaries.append(chunk_summary)
            logger.info(f"청크 {i+1}/{len(chunks)} 요약 완료: {len(chunk_summary)}자")
        
        # 2단계: 청크 요약들을 통합하여 최종 요약
        final_summary = await _integrate_summaries(ollama_client, model_name, chunk_summaries, max_length, category, executor)
        
        logger.info(f"최종 요약 완료: {len(final_summary)}자")
        return final_summary
        
    finally:
        executor.shutdown(wait=False)