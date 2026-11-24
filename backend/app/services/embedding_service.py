
from functools import lru_cache
from typing import Sequence

from fastembed import TextEmbedding
from sqlalchemy.orm import Session

from ..models.document_segment import DocumentSegment
from ..models.document_embedding import DocumentEmbedding


EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSIONS = 384


@lru_cache(maxsize=1)
def get_embedding_model() -> TextEmbedding:
    """
    Load the pre-trained embedding model once per application process.
    """

    return TextEmbedding(
        model_name=EMBEDDING_MODEL_NAME
    )


def generate_embeddings(
    texts: Sequence[str],
) -> list[list[float]]:
    """
    Generate normalized text embeddings using FastEmbed.
    """

    if not texts:
        return []

    cleaned_texts = []

    for text in texts:
        if not isinstance(text, str) or not text.strip():
            raise ValueError(
                "Embedding input must contain non-empty text."
            )

        cleaned_texts.append(text.strip())

    model = get_embedding_model()

    vectors = model.embed(cleaned_texts)

    embeddings = [
        [float(value) for value in vector]
        for vector in vectors
    ]

    if len(embeddings) != len(cleaned_texts):
        raise RuntimeError(
            "Embedding count does not match input text count."
        )

    for embedding in embeddings:
        if len(embedding) != EMBEDDING_DIMENSIONS:
            raise RuntimeError(
                f"Expected {EMBEDDING_DIMENSIONS} dimensions, "
                f"received {len(embedding)}."
            )

    return embeddings


def save_segment_embeddings(
    db: Session,
    segments: Sequence[DocumentSegment],
) -> list[DocumentEmbedding]:
    """
    Generate and stage embeddings for document segments.

    Existing embeddings for the same segment and model are skipped.

    This function does not commit the database transaction.
    The calling service controls the commit.
    """

    if not segments:
        return []

    segment_ids = [segment.id for segment in segments]

    if any(segment_id is None for segment_id in segment_ids):
        raise ValueError(
            "All document segments must be saved before embedding."
        )

    if len(segment_ids) != len(set(segment_ids)):
        raise ValueError(
            "Duplicate segment IDs were provided."
        )

    existing_embeddings = (
        db.query(DocumentEmbedding.segment_id)
        .filter(
            DocumentEmbedding.segment_id.in_(segment_ids),
            DocumentEmbedding.model_name == EMBEDDING_MODEL_NAME,
        )
        .all()
    )

    existing_segment_ids = {
        row[0] for row in existing_embeddings
    }

    missing_segments = [
        segment
        for segment in segments
        if segment.id not in existing_segment_ids
    ]

    if not missing_segments:
        return []

    texts = [
        segment.content
        for segment in missing_segments
    ]

    vectors = generate_embeddings(texts)

    embedding_records = []

    for segment, vector in zip(missing_segments, vectors):
        record = DocumentEmbedding(
            segment_id=segment.id,
            model_name=EMBEDDING_MODEL_NAME,
            dimensions=EMBEDDING_DIMENSIONS,
            embedding=vector,
        )

        db.add(record)
        embedding_records.append(record)

    db.flush()

    return embedding_records
