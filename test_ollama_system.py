#!/usr/bin/env python3
"""
Ollama 기반 3서버 시스템 테스트 스크립트
"""
import asyncio
import aiohttp
import json
import time
from typing import Dict, Any
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 서버 설정
SERVERS = {
    "standardizer": "http://localhost:8000",
    "summary": "http://localhost:8100", 
    "news": "http://localhost:8200",
    "ollama": "http://localhost:11434"
}

# 테스트 데이터
SAMPLE_DART_TEXT = """
[사업의 개요]
당사는 2020년에 설립된 IT 솔루션 기업으로, 주력 사업은 클라우드 기반 데이터 분석 플랫폼 개발 및 운영입니다. 
주요 고객은 금융기관 및 대기업이며, 매출의 80%를 차지하고 있습니다. 
2024년 3분기 매출액은 150억원으로 전년 동기 대비 25% 증가하였습니다.
사업장은 서울 강남구에 본사를 두고 있으며, 임직원 수는 총 120명입니다.
"""

class SystemTester:
    """시스템 테스트 클래스"""
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def check_server_health(self, server_name: str, url: str) -> bool:
        """서버 헬스체크"""
        try:
            async with self.session.get(f"{url}/health", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ {server_name} 서버 정상: {data}")
                    return True
                else:
                    logger.error(f"❌ {server_name} 서버 헬스체크 실패: HTTP {response.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ {server_name} 서버 연결 실패: {e}")
            return False
    
    async def check_ollama_models(self) -> bool:
        """Ollama 모델 확인"""
        try:
            async with self.session.get(f"{SERVERS['ollama']}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    models = [model['name'] for model in data.get('models', [])]
                    logger.info(f"✅ Ollama 사용 가능한 모델: {models}")
                    
                    # 필요한 모델 확인
                    required_models = [
                        'qwen2.5:1.8b-instruct-q4_0',
                        'qwen2.5:0.5b-instruct-fp16'
                    ]
                    
                    missing_models = [m for m in required_models if m not in models]
                    if missing_models:
                        logger.warning(f"⚠️  누락된 모델: {missing_models}")
                        return False
                    
                    return True
                else:
                    logger.error(f"❌ Ollama 모델 조회 실패: HTTP {response.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ Ollama 연결 실패: {e}")
            return False
    
    async def test_standardizer(self, mapping_id: int = 123, chapter: int = 1) -> Dict[str, Any]:
        """표준화 서버 테스트"""
        logger.info("🔄 표준화 서버 테스트 시작...")
        
        payload = {
            "mapping_id": mapping_id,
            "chapter": chapter,
            "content": SAMPLE_DART_TEXT,
            "file_path": f"test_{mapping_id}_{chapter}.txt"
        }
        
        try:
            async with self.session.post(
                f"{SERVERS['standardizer']}/standardize",
                json=payload,
                timeout=60
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ 표준화 완료: {len(data['standardized_content'])}자")
                    return data
                else:
                    text = await response.text()
                    logger.error(f"❌ 표준화 실패: HTTP {response.status}, {text}")
                    return {}
        except Exception as e:
            logger.error(f"❌ 표준화 요청 실패: {e}")
            return {}
    
    async def test_summary(self, mapping_id: int = 123, chapter: int = 1) -> Dict[str, Any]:
        """요약 서버 테스트"""
        logger.info("🔄 요약 서버 테스트 시작...")
        
        payload = {
            "mapping_id": mapping_id,
            "chapter": chapter,
            "content": SAMPLE_DART_TEXT,
            "max_length": 300
        }
        
        try:
            async with self.session.post(
                f"{SERVERS['summary']}/summarize",
                json=payload,
                timeout=60
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ 요약 완료: {len(data['summary'])}자, 키워드: {data['keywords']}")
                    return data
                else:
                    text = await response.text()
                    logger.error(f"❌ 요약 실패: HTTP {response.status}, {text}")
                    return {}
        except Exception as e:
            logger.error(f"❌ 요약 요청 실패: {e}")
            return {}
    
    async def test_news_generation(self, mapping_id: int = 123) -> Dict[str, Any]:
        """뉴스 생성 서버 테스트"""
        logger.info("🔄 뉴스 생성 서버 테스트 시작...")
        
        payload = {
            "mapping_id": mapping_id,
            "summaries": {
                1: "당사는 IT 솔루션 기업으로 클라우드 데이터 분석 플랫폼을 개발합니다. 2024년 3분기 매출 150억원으로 전년 대비 25% 증가했습니다."
            },
            "keywords": ["클라우드", "데이터분석", "매출증가"]
        }
        
        try:
            async with self.session.post(
                f"{SERVERS['news']}/generate-news",
                json=payload,
                timeout=60
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ 뉴스 생성 완료: {len(data['news_summary'])}자")
                    return data
                else:
                    text = await response.text()
                    logger.error(f"❌ 뉴스 생성 실패: HTTP {response.status}, {text}")
                    return {}
        except Exception as e:
            logger.error(f"❌ 뉴스 생성 요청 실패: {e}")
            return {}
    
    async def test_server_status(self) -> Dict[str, Any]:
        """모든 서버 상태 조회"""
        logger.info("🔄 서버 상태 조회...")
        
        results = {}
        for server_name in ["standardizer", "summary", "news"]:
            try:
                async with self.session.get(
                    f"{SERVERS[server_name]}/status",
                    timeout=10
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        results[server_name] = data
                        logger.info(f"✅ {server_name} 상태: {data.get('status', 'unknown')}")
                    else:
                        logger.error(f"❌ {server_name} 상태 조회 실패: HTTP {response.status}")
            except Exception as e:
                logger.error(f"❌ {server_name} 상태 조회 실패: {e}")
        
        return results
    
    async def run_full_pipeline_test(self) -> bool:
        """전체 파이프라인 테스트"""
        logger.info("🚀 전체 파이프라인 테스트 시작...")
        
        mapping_id = int(time.time())  # 고유 ID
        chapter = 1
        
        # 1. 표준화 테스트
        standardize_result = await self.test_standardizer(mapping_id, chapter)
        if not standardize_result:
            return False
        
        await asyncio.sleep(2)  # 잠시 대기
        
        # 2. 요약 테스트
        summary_result = await self.test_summary(mapping_id, chapter)
        if not summary_result:
            return False
        
        await asyncio.sleep(2)  # 잠시 대기
        
        # 3. 뉴스 생성 테스트
        news_result = await self.test_news_generation(mapping_id)
        if not news_result:
            return False
        
        logger.info("✅ 전체 파이프라인 테스트 성공!")
        return True
    
    async def run_all_tests(self) -> bool:
        """모든 테스트 실행"""
        logger.info("=" * 60)
        logger.info("🧪 Ollama 기반 LLM 시스템 통합 테스트")
        logger.info("=" * 60)
        
        # 1. 서버 헬스체크
        logger.info("\n1️⃣ 서버 헬스체크")
        health_results = {}
        for server_name, url in SERVERS.items():
            if server_name == "ollama":
                health_results[server_name] = await self.check_ollama_models()
            else:
                health_results[server_name] = await self.check_server_health(server_name, url)
        
        if not all(health_results.values()):
            logger.error("❌ 일부 서버가 정상 동작하지 않습니다.")
            return False
        
        # 2. 상태 조회 테스트
        logger.info("\n2️⃣ 서버 상태 조회")
        await self.test_server_status()
        
        # 3. 개별 서버 기능 테스트
        logger.info("\n3️⃣ 개별 서버 기능 테스트")
        
        # 4. 전체 파이프라인 테스트
        logger.info("\n4️⃣ 전체 파이프라인 테스트")
        pipeline_success = await self.run_full_pipeline_test()
        
        # 결과 요약
        logger.info("\n" + "=" * 60)
        if pipeline_success:
            logger.info("🎉 모든 테스트가 성공적으로 완료되었습니다!")
            logger.info("✅ 시스템이 정상 동작합니다.")
        else:
            logger.error("❌ 테스트 실패. 시스템을 점검해주세요.")
        logger.info("=" * 60)
        
        return pipeline_success

async def main():
    """메인 함수"""
    async with SystemTester() as tester:
        success = await tester.run_all_tests()
        return success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("🛑 테스트 중단됨")
        exit(1)
    except Exception as e:
        logger.error(f"💥 예상치 못한 오류: {e}")
        exit(1)