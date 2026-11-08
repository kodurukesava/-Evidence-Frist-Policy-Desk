
from pydantic import BaseModel, Field
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

    # Duplicate detection metadata
    duplicate_evidence_ids: list[str] = Field(default_factory=list)
    duplicate_source_count: int = 1


class EvidenceResponse(BaseModel):
    query: str
    workspace_id: int
    answer: str
    status: str

    evidence: list[EvidenceItem]
    citations: list[str]
    citations_valid: bool

    # Evidence deduplication statistics
    unique_evidence_count: int = 0
    duplicate_evidence_count: int = 0
