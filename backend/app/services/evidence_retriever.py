
import re

from sqlalchemy.orm import Session

from .document_search import search_document_segments
from .semantic_search import search_semantic_segments
from .duplicate_detector import detect_duplicate_evidence


# Remove only words that usually add little search meaning.
# Keep policy obligations, actors, conditions, and negations.
STOP_WORDS = {
    "what", "which", "who", "where", "when", "why", "how",
    "do", "does", "did", "is", "are", "was", "were",
    "the", "a", "an",
    "in", "on", "at", "to", "for", "of", "with", "by",
    "and", "or",
}


RRF_K = 60


def prepare_search_query(query: str) -> str:
    """Remove common question filler while preserving policy terms."""

    if not isinstance(query, str) or not query.strip():
        raise ValueError("Search query cannot be empty.")

    words = re.findall(r"[\w]+", query.casefold())

    keywords = [
        word for word in words
        if word not in STOP_WORDS
    ]

    # Retain the original query if every word was filtered.
    return " ".join(keywords) if keywords else query.strip()


def reciprocal_rank_fusion(
    keyword_results: list[dict],
    semantic_results: list[dict],
    limit: int = 10,
    k: int = RRF_K,
) -> list[dict]:
    """
    Combine keyword and semantic rankings using RRF.

    RRF score = sum(1 / (k + rank)) across retrieval methods.

    Segment IDs identify the same evidence passage across both
    retrieval methods. The original evidence fields are retained.
    """

    fused = {}

    for results in (keyword_results, semantic_results):
        for rank, result in enumerate(results, start=1):
            segment_id = result["segment_id"]

            if segment_id not in fused:
                fused[segment_id] = {
                    **result,
                    "relevance_score": 0.0,
                    "keyword_rank": None,
                    "semantic_rank": None,
                }

            fused[segment_id]["relevance_score"] += (
                1.0 / (k + rank)
            )

            if results is keyword_results:
                fused[segment_id]["keyword_rank"] = rank
            else:
                fused[segment_id]["semantic_rank"] = rank

    ranked = sorted(
        fused.values(),
        key=lambda item: (
            -item["relevance_score"],
            item["segment_id"],
        ),
    )

    return ranked[:max(1, min(limit, 50))]


def retrieve_evidence(
    db: Session,
    workspace_id: int,
    query: str,
    limit: int = 10,
):
    """
    Retrieve evidence using hybrid keyword and semantic search.

    Both retrieval methods apply workspace, current-version,
    and active-document filters before returning candidates.

    Results are merged with RRF, then duplicate passages are
    grouped without changing their original document records.
    """

    if not query or not query.strip():
        raise ValueError("Search query cannot be empty.")

    limit = max(1, min(limit, 50))
    search_query = prepare_search_query(query)

    # Retrieve a broader candidate pool from both methods.
    candidate_limit = min(max(limit * 5, 20), 50)

    keyword_results = search_document_segments(
        db=db,
        workspace_id=workspace_id,
        query=search_query,
        limit=candidate_limit,
    )

    semantic_results = search_semantic_segments(
        db=db,
        workspace_id=workspace_id,
        query=query.strip(),
        limit=candidate_limit,
    )

    # Combine both rankings using Reciprocal Rank Fusion.
    search_results = reciprocal_rank_fusion(
        keyword_results=keyword_results,
        semantic_results=semantic_results,
        limit=candidate_limit,
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

    return unique_evidence[:limit]
