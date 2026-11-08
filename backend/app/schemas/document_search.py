
from pydantic import BaseModel
from typing import Optional


class DocumentSearchResult(BaseModel):
    segment_id: int
    version_id: int
    document_id: int
    document_name: str
    workspace_id: int
    segment_index: int
    section_title: Optional[str] = None
    content: str
    relevance_score: float


class DocumentSearchResponse(BaseModel):
    query: str
    workspace_id: int
    total_results: int
    results: list[DocumentSearchResult]
