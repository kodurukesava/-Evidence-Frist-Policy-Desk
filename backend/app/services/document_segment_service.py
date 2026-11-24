
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import logging

from sqlalchemy.orm import Session

from ..models.document import Document
from ..models.document_version import DocumentVersion
from ..models.document_segment import DocumentSegment
from .document_chunker import split_into_chunks
from .embedding_service import save_segment_embeddings


logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DOCUMENT_STORAGE_DIR = PROJECT_ROOT / "data" / "documents"


def calculate_file_checksum(file_path: Path) -> str:
    """Calculate the SHA-256 checksum of a document."""

    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(block)

    return sha256.hexdigest()


def _generate_and_save_embeddings(
    db: Session,
    segments: list[DocumentSegment],
) -> None:
    """
    Generate and save embeddings in a separate transaction.

    Embedding failures must not undo an already-saved document version
    or its segments. Failures are logged so they can be investigated
    and retried later.
    """

    try:
        save_segment_embeddings(db, segments)
        db.commit()

        logger.info(
            "Successfully processed embeddings for %s segments.",
            len(segments),
        )

    except Exception:
        db.rollback()

        logger.exception(
            "Embedding generation failed for saved document segments. "
            "The document and its segments remain available."
        )


def create_document_version_and_segments(
    db: Session,
    document: Document,
):
    """
    Create a document version, save its segments, and generate embeddings.

    Document versions and segments are committed before embedding
    generation so embedding failures cannot destroy uploaded documents.
    """

    try:
        # 1. Validate extracted text
        if not document.extracted_text or not document.extracted_text.strip():
            raise ValueError(
                "Document has no extracted text. Cannot generate segments."
            )

        # 2. Locate the stored document
        file_path = DOCUMENT_STORAGE_DIR / document.stored_filename

        if not file_path.is_file():
            raise FileNotFoundError(
                f"Stored document not found: {file_path}"
            )

        # 3. Calculate document checksum
        checksum = calculate_file_checksum(file_path)

        # 4. Check the latest document version
        latest_version = (
            db.query(DocumentVersion)
            .filter(DocumentVersion.document_id == document.id)
            .order_by(DocumentVersion.version_number.desc())
            .first()
        )

        # 5. Reuse an existing version if its checksum matches
        if latest_version and latest_version.checksum == checksum:
            version = latest_version

            existing_segments = (
                db.query(DocumentSegment)
                .filter(
                    DocumentSegment.document_version_id == version.id
                )
                .order_by(DocumentSegment.segment_index)
                .all()
            )

            if existing_segments:
                # Retry missing embeddings for an existing version.
                _generate_and_save_embeddings(db, existing_segments)

                return version, existing_segments

        else:
            # 6. Mark the previous version as no longer current
            if latest_version:
                latest_version.is_current = False
                latest_version.effective_to = datetime.now(timezone.utc)

            # 7. Create a new document version
            next_version_number = (
                latest_version.version_number + 1
                if latest_version
                else 1
            )

            version = DocumentVersion(
                document_id=document.id,
                version_number=next_version_number,
                checksum=checksum,
                storage_path=str(file_path),
                effective_from=datetime.now(timezone.utc),
                is_current=True,
            )

            db.add(version)
            db.flush()

        # 8. Split extracted text into chunks
        chunks = split_into_chunks(document.extracted_text)

        if not chunks:
            raise ValueError("No chunks could be generated.")

        # 9. Save chunks as document segments
        segments = []

        for index, chunk in enumerate(chunks, start=1):
            segment = DocumentSegment(
                document_version_id=version.id,
                segment_index=index,
                segment_type="text",
                section_title=None,
                content=chunk,
            )

            db.add(segment)
            segments.append(segment)

        # 10. Commit document version and segments first
        db.commit()

        # Refresh database objects
        db.refresh(version)

        for segment in segments:
            db.refresh(segment)

        # 11. Generate embeddings in a separate transaction
        _generate_and_save_embeddings(db, segments)

        return version, segments

    except Exception:
        db.rollback()
        raise
