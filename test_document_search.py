
from backend.app.database import SessionLocal
from backend.app.services.document_search import (
    search_document_segments,
)

db = SessionLocal()

try:
    results = search_document_segments(
        db=db,
        workspace_id=1,
        query="Attendance Policy",
        limit=10,
    )

    print("\n========== DOCUMENT SEARCH TEST ==========\n")
    print("Search query: Attendance Policy")
    print("Workspace ID: 1")
    print("Results found:", len(results))

    for index, result in enumerate(results, start=1):
        print(f"\nRESULT {index}")
        print("-" * 45)

        print("Document ID:", result["document_id"])
        print("Document:", result["document_name"])
        print("Version ID:", result["version_id"])
        print("Segment ID:", result["segment_id"])
        print("Segment index:", result["segment_index"])
        print("Relevance score:", result["relevance_score"])
        print("Content:")
        print(result["content"])

    print("\nDOCUMENT SEARCH TEST: PASSED")

except Exception as error:
    print("\nDOCUMENT SEARCH TEST: FAILED")
    print("Error:", error)

finally:
    db.close()
