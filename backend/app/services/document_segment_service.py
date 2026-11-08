
from datetime import datetime, timezone
from pathlib import Path
import hashlib

from sqlalchemy.orm import Session

from ..models.document import Document
from ..models.document_version import DocumentVersion
from ..models.document_segment import DocumentSegment
from .document_chunker import split_into_chunks


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DOCUMENT_STORAGE_DIR = PROJECT_ROOT / "data" / "documents"


def calculate_file_checksum(file_path: Path) -> str:
    """Calculate the SHA-256 checksum of a document."""

    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(block)

    return sha256.hexdigest()


def create_document_version_and_segments(
    db: Session,
    document: Document,
):
    """
    Create a document version and save its extracted text as segments.
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

        # 10. Commit database transaction
        db.commit()

        # Refresh database objects
        db.refresh(version)

        for segment in segments:
            db.refresh(segment)

        return version, segments

    except Exception:
        db.rollback()
        raise
