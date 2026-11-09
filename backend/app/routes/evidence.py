
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy.orm import Session
from groq import GroqError

from ..database import get_db
from ..models.user import User

from ..dependencies import (
    get_current_user,
    get_accessible_workspace,
)

from ..services.evidence_retriever import retrieve_evidence
from ..services.answer_generator import generate_grounded_answer
from ..services.conflict_detector import detect_conflicts

from ..schemas.evidence import EvidenceResponse, EvidenceItem
from ..schemas.conflict import ConflictResponse


router = APIRouter(
    prefix="/evidence",
    tags=["Evidence"],
)


# --------------------------------------------------
# POLICY CONFLICT DETECTION API
# --------------------------------------------------

@router.get(
    "/conflicts/{workspace_id}",
    response_model=ConflictResponse,
)
def get_policy_conflicts(
    workspace_id: int,
    query: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Detect potential policy conflicts using evidence
    from current document versions in an accessible workspace.
    """

    # Step 1: Verify workspace access
    workspace = get_accessible_workspace(
        workspace_id=workspace_id,
        current_user=current_user,
        db=db,
    )

    # Step 2: Retrieve evidence
    try:
        evidence_items = retrieve_evidence(
            db=db,
            workspace_id=workspace_id,
            query=query,
            limit=50,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    # Step 3: Detect potential conflicts
    conflict_result = detect_conflicts(evidence_items)

    # Step 4: Return conflict report
    return ConflictResponse(
        query=query,
        workspace_id=workspace_id,
        total_evidence_compared=conflict_result[
            "total_evidence_compared"
        ],
        potential_conflict_count=conflict_result[
            "potential_conflict_count"
        ],
        conflicts=conflict_result["conflicts"],
    )


# --------------------------------------------------
# EVIDENCE RETRIEVAL AND GROUNDED ANSWER API
# --------------------------------------------------

@router.get(
    "/{workspace_id}",
    response_model=EvidenceResponse,
)
def get_evidence(
    workspace_id: int,
    query: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    # Step 1: Verify workspace access
    workspace = get_accessible_workspace(
        workspace_id=workspace_id,
        current_user=current_user,
        db=db,
    )

    # Step 2: Retrieve deduplicated evidence
    try:
        evidence_items = retrieve_evidence(
            db=db,
            workspace_id=workspace_id,
            query=query,
            limit=10,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    # Step 3: Calculate duplicate statistics
    unique_evidence_count = len(evidence_items)

    duplicate_evidence_count = sum(
        len(item.get("duplicate_evidence_ids", []))
        for item in evidence_items
    )

    # Step 4: Generate a grounded answer
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

    # Step 5: Convert evidence into response objects
    evidence = [
        EvidenceItem(**item)
        for item in evidence_items
    ]

    # Step 6: Return the complete response
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
