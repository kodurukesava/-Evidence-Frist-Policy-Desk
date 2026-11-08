from pydantic import BaseModel


class ConflictEvidence(BaseModel):
    evidence_id: str
    document_id: int
    document_name: str
    content: str


class PotentialConflict(BaseModel):
    conflict_type: str
    status: str

    evidence_a: ConflictEvidence
    evidence_b: ConflictEvidence

    shared_terms: list[str]
    topic_overlap: float


class ConflictResponse(BaseModel):
    query: str
    workspace_id: int

    total_evidence_compared: int
    potential_conflict_count: int

    conflicts: list[PotentialConflict]