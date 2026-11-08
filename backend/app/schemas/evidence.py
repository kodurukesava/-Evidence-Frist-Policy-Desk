from pydantic import BaseModel
from typing import Optional


class EvidenceItem(BaseModel):
    evidence_id: str
    document_id: int
    document_name: str
    workspace_id: int
    version_id: int
    segment_id: int
    segment_index: int
    section_title: Optional[str] = None
    content: str
    relevance_score: float


class EvidenceResponse(BaseModel):
    query: str
    workspace_id: int
    answer: str
    status: str
    evidence: list[EvidenceItem]
    citations: list[str]
    citations_valid: bool