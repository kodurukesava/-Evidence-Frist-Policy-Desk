
from backend.app.database import SessionLocal
from backend.app.models.document import Document
from backend.app.models.document_version import DocumentVersion
from backend.app.models.document_segment import DocumentSegment
from backend.app.services.embedding_service import (
    save_segment_embeddings,
    EMBEDDING_MODEL_NAME,
)


def main():
    db = SessionLocal()

    try:
        segments = (
            db.query(DocumentSegment)
            .join(
                DocumentVersion,
                DocumentVersion.id
                == DocumentSegment.document_version_id,
            )
            .join(
                Document,
                Document.id == DocumentVersion.document_id,
            )
            .filter(
                Document.workspace_id == 1,
                DocumentVersion.is_current.is_(True),
                Document.lifecycle_status == "active",
            )
            .order_by(Document.id, DocumentSegment.id)
            .all()
        )

        print(f"Found {len(segments)} active segments.")

        created = save_segment_embeddings(db, segments)

        db.commit()

        print(f"New embeddings created: {len(created)}")
        print(f"Embedding model: {EMBEDDING_MODEL_NAME}")
        print("Backfill completed successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
