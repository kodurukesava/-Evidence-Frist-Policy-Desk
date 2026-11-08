
from sqlalchemy.orm import Session

from .document_search import search_document_segments


def retrieve_evidence(
    db: Session,
    workspace_id: int,
    query: str,
    limit: int = 10,
):
    """
    Retrieve evidence passages from the current document versions
    within a specified workspace.

    Each passage receives a stable evidence identifier
    based on its document, version, and segment.
    """

    # Step 1: Search document segments
    search_results = search_document_segments(
        db=db,
        workspace_id=workspace_id,
        query=query,
        limit=limit,
    )

    # Step 2: Prepare evidence collection
    evidence_items = []

    # Step 3: Process each search result
    for result in search_results:

        # Generate a unique evidence ID
        evidence_id = (
            f"DOC-{result['document_id']}"
            f"-VER-{result['version_id']}"
            f"-SEG-{result['segment_id']}"
        )

        # Build evidence details
        evidence = {
            "evidence_id": evidence_id,
            "document_id": result["document_id"],
            "document_name": result["document_name"],
            "workspace_id": result["workspace_id"],
            "version_id": result["version_id"],
            "segment_id": result["segment_id"],
            "segment_index": result["segment_index"],
            "section_title": result["section_title"],
            "content": result["content"],
            "relevance_score": result["relevance_score"],
        }

        evidence_items.append(evidence)

    # Step 4: Return retrieved evidence
    return evidence_items
