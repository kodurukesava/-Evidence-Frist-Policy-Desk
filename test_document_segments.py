
from backend.app.database import SessionLocal
from backend.app.models.document import Document
from backend.app.services.document_segment_service import (
    create_document_version_and_segments,
)

db = SessionLocal()

try:
    # Find the existing sample.txt document
    document = (
        db.query(Document)
        .filter(Document.id == 7)
        .first()
    )

    if not document:
        print("ERROR: Document ID 7 was not found.")
    else:
        print("Document found:", document.original_filename)
        print("Document ID:", document.id)

        # Create document version and save chunks
        version, segments = create_document_version_and_segments(
            db=db,
            document=document,
        )

        print("\n========== DOCUMENT VERSION ==========")
        print("Version ID:", version.id)
        print("Version Number:", version.version_number)
        print("Checksum:", version.checksum)
        print("Current Version:", version.is_current)

        print("\n========== DOCUMENT SEGMENTS ==========")

        for segment in segments:
            print(f"\nSegment {segment.segment_index}")
            print("-" * 40)
            print(segment.content)
            print("Characters:", len(segment.content))

        print("\nTotal segments created:", len(segments))
        print("\nDOCUMENT SEGMENT TEST: PASSED")

except Exception as error:
    print("\nDOCUMENT SEGMENT TEST: FAILED")
    print("Error:", error)

finally:
    db.close()
