"""
기본 서비스 클래스
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from utils.logger import get_logger


class BaseService(ABC):
    """모든 서비스의 기본 클래스"""

    def __init__(self, name: Optional[str] = None):
        self.name = name or self.__class__.__name__
        self.logger = get_logger(self.name)
        self._initialized = False

    async def initialize(self) -> None:
        """서비스 초기화"""
        if self._initialized:
            return

        try:
            await self._setup()
            self._initialized = True
            self.logger.info(f"{self.name} service initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize {self.name}: {e}")
            raise

    async def shutdown(self) -> None:
        """서비스 종료"""
        if not self._initialized:
            return

        try:
            await self._cleanup()
            self._initialized = False
            self.logger.info(f"{self.name} service shutdown")
        except Exception as e:
            self.logger.error(f"Error during {self.name} shutdown: {e}")

    @abstractmethod
    async def _setup(self) -> None:
        """구체적인 초기화 로직 (하위 클래스에서 구현)"""
        pass

    async def _cleanup(self) -> None:
        """구체적인 정리 로직 (하위 클래스에서 선택적 구현)"""
        pass

    def get_status(self) -> Dict[str, Any]:
        """서비스 상태 반환"""
        return {
            "name": self.name,
            "initialized": self._initialized
        }

    @property
    def is_initialized(self) -> bool:
        """초기화 상태 확인"""
        return self._initialized