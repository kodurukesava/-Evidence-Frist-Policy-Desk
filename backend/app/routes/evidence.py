from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.services.evidence_retriever import retrieve_evidence
from backend.app.services.citation_validator import validate_citations
from backend.app.schemas.evidence import EvidenceResponse, EvidenceItem

router = APIRouter(
    prefix="/evidence",
    tags=["Evidence"],
)


@router.get("/{workspace_id}", response_model=EvidenceResponse)
def get_evidence(
    workspace_id: int,
    query: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    evidence_items = retrieve_evidence(
        db=db,
        workspace_id=workspace_id,
        query=query,
        limit=10,
    )

    if not evidence_items:
        return EvidenceResponse(
            query=query,
            workspace_id=workspace_id,
            answer="Insufficient evidence.",
            status="insufficient_evidence",
            evidence=[],
            citations=[],
            citations_valid=True,
        )

    evidence = [
        EvidenceItem(**item)
        for item in evidence_items
    ]

    citations = [
        item["evidence_id"]
        for item in evidence_items
    ]
    validation = validate_citations(
        answer_citations=citations,
        retrieved_evidence=evidence_items,
    )

    return EvidenceResponse(
        query=query,
        workspace_id=workspace_id,
        answer="Evidence retrieved successfully. AI answer generation is not yet enabled.",
        status="evidence_retrieved",
        evidence=evidence,
        citations=citations,
        citations_valid=validation["is_valid"],
    )
