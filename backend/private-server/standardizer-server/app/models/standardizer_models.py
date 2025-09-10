from pydantic import BaseModel

class StandardizeRequest(BaseModel):
    """텍스트 표준화 요청 모델"""
    mapping_id: int
    chapter: int
    content: str
    file_path: str = ""

class StandardizeResponse(BaseModel):
    """텍스트 표준화 응답 모델"""
    mapping_id: int
    chapter: int
    standardized_content: str
    status: str = "completed"