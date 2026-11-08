
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from groq import GroqError

from backend.app.database import get_db
from backend.app.services.evidence_retriever import retrieve_evidence
from backend.app.services.answer_generator import generate_grounded_answer
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
    # Step 1: Retrieve deduplicated evidence.
    evidence_items = retrieve_evidence(
        db=db,
        workspace_id=workspace_id,
        query=query,
        limit=10,
    )

    # Step 2: Calculate duplicate statistics.
    unique_evidence_count = len(evidence_items)

    duplicate_evidence_count = sum(
        len(item.get("duplicate_evidence_ids", []))
        for item in evidence_items
    )

    # Step 3: Generate a grounded answer.
    try:
        answer_result = generate_grounded_answer(
            question=query,
            retrieved_evidence=evidence_items,
        )

    except (GroqError, RuntimeError):
        raise HTTPException(
            status_code=502,
            detail="AI answer generation failed. Please try again.",
        )

    # Step 4: Convert evidence into response objects.
    evidence = [
        EvidenceItem(**item)
        for item in evidence_items
    ]

    # Step 5: Return the complete response.
    return EvidenceResponse(
        query=query,
        workspace_id=workspace_id,
        answer=answer_result["answer"],
        status=answer_result["status"],
        evidence=evidence,
        citations=answer_result["citations"],
        citations_valid=answer_result["citations_valid"],
        unique_evidence_count=unique_evidence_count,
        duplicate_evidence_count=duplicate_evidence_count,
    )
