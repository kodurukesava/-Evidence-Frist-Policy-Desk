import re

from sqlalchemy.orm import Session

from .document_search import search_document_segments
from .duplicate_detector import detect_duplicate_evidence


STOP_WORDS = {
    "what", "which", "who", "where", "when", "why", "how",
    "must", "should", "could", "would", "can", "do", "does",
    "did", "is", "are", "was", "were", "the", "a", "an",
    "in", "on", "at", "to", "for", "of", "with", "by",
    "and", "or", "employees",
}


def prepare_search_query(query: str) -> str:
    """Remove common question words before keyword retrieval."""

    words = re.findall(r"[\w]+", query.lower())

    keywords = [
        word for word in words
        if word not in STOP_WORDS
    ]

    return " ".join(keywords) if keywords else query


def retrieve_evidence(
    db: Session,
    workspace_id: int,
    query: str,
    limit: int = 10,
):
    """
    Retrieve evidence from current document versions
    within a specified workspace.

    Identical passages are grouped so duplicate copies
    are not treated as independent supporting evidence.
    Original document records remain unchanged.
    """

    search_query = prepare_search_query(query)

    search_results = search_document_segments(
        db=db,
        workspace_id=workspace_id,
        query=search_query,
        limit=limit,
    )

    evidence_items = []

    for result in search_results:
        evidence_id = (
            f"DOC-{result['document_id']}"
            f"-VER-{result['version_id']}"
            f"-SEG-{result['segment_id']}"
        )

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

    # Group identical passages and retain one canonical passage.
    deduplication_result = detect_duplicate_evidence(
        evidence_items
    )

    unique_evidence = deduplication_result["unique_evidence"]

    # Preserve the IDs of duplicate sources as metadata.
    duplicate_groups = {
        group["primary_evidence_id"]: group
        for group in deduplication_result["duplicate_groups"]
    }

    for evidence in unique_evidence:
        group = duplicate_groups.get(evidence["evidence_id"])

        if group:
            evidence["duplicate_evidence_ids"] = (
                group["duplicate_evidence_ids"]
            )
            evidence["duplicate_source_count"] = (
                group["source_count"]
            )
        else:
            evidence["duplicate_evidence_ids"] = []
            evidence["duplicate_source_count"] = 1

    return unique_evidence