
import math

from sqlalchemy.orm import Session

from ..models.document_embedding import DocumentEmbedding
from ..models.document_segment import DocumentSegment
from ..models.document_version import DocumentVersion
from ..models.document import Document
from .embedding_service import (
    EMBEDDING_MODEL_NAME,
    generate_embeddings,
)


def cosine_similarity(
    vector_a: list[float],
    vector_b: list[float],
) -> float:
    """Calculate cosine similarity between two vectors."""

    if len(vector_a) != len(vector_b):
        raise ValueError("Embedding dimensions must match.")

    dot_product = sum(
        a * b for a, b in zip(vector_a, vector_b)
    )

    norm_a = math.sqrt(sum(value * value for value in vector_a))
    norm_b = math.sqrt(sum(value * value for value in vector_b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)


def search_semantic_segments(
    db: Session,
    workspace_id: int,
    query: str,
    limit: int = 10,
) -> list[dict]:
    """
    Retrieve semantically similar segments.

    Workspace, current-version, active-document and embedding-model
    filters are applied in SQL before similarity ranking.
    """

    if not query or not query.strip():
        raise ValueError("Semantic search query cannot be empty.")

    limit = max(1, min(limit, 50))

    # Generate the question embedding locally.
    query_embedding = generate_embeddings([query.strip()])[0]

    # Retrieve only authorized-scope candidates.
    candidates = (
        db.query(
            DocumentSegment.id.label("segment_id"),
            DocumentSegment.document_version_id.label("version_id"),
            DocumentVersion.document_id.label("document_id"),
            Document.original_filename.label("document_name"),
            Document.workspace_id.label("workspace_id"),
            DocumentSegment.segment_index.label("segment_index"),
            DocumentSegment.section_title.label("section_title"),
            DocumentSegment.content.label("content"),
            DocumentEmbedding.embedding.label("embedding"),
        )
        .join(
            DocumentEmbedding,
            DocumentEmbedding.segment_id == DocumentSegment.id,
        )
        .join(
            DocumentVersion,
            DocumentVersion.id == DocumentSegment.document_version_id,
        )
        .join(
            Document,
            Document.id == DocumentVersion.document_id,
        )
        .filter(
            Document.workspace_id == workspace_id,
            DocumentVersion.is_current.is_(True),
            Document.lifecycle_status == "active",
            DocumentEmbedding.model_name == EMBEDDING_MODEL_NAME,
        )
        .all()
    )

    ranked_results = []

    for candidate in candidates:
        similarity = cosine_similarity(
            query_embedding,
            candidate.embedding,
        )

        result = {
            "segment_id": candidate.segment_id,
            "version_id": candidate.version_id,
            "document_id": candidate.document_id,
            "document_name": candidate.document_name,
            "workspace_id": candidate.workspace_id,
            "segment_index": candidate.segment_index,
            "section_title": candidate.section_title,
            "content": candidate.content,
            "relevance_score": similarity,
        }

        ranked_results.append(result)

    ranked_results.sort(
        key=lambda item: (
            -item["relevance_score"],
            item["segment_id"],
        )
    )

    return ranked_results[:limit]
