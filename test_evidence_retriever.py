
from backend.app.database import SessionLocal
from backend.app.services.evidence_retriever import retrieve_evidence

db = SessionLocal()

try:
    evidence = retrieve_evidence(
        db=db,
        workspace_id=1,
        query="Attendance Policy",
        limit=10,
    )

    print("\n========== EVIDENCE RETRIEVAL TEST ==========\n")

    print("Evidence items retrieved:", len(evidence))

    for index, item in enumerate(evidence, start=1):
        print(f"\nEVIDENCE {index}")
        print("-" * 50)

        print("Evidence ID:", item["evidence_id"])
        print("Document:", item["document_name"])
        print("Document ID:", item["document_id"])
        print("Version ID:", item["version_id"])
        print("Segment ID:", item["segment_id"])
        print("Relevance:", item["relevance_score"])

        print("\nExact source passage:")
        print(item["content"])

    assert len(evidence) > 0, "No evidence retrieved."

    assert all(
        item["content"].strip()
        and item["evidence_id"]
        for item in evidence
    ), "Invalid evidence item."

    print("\nEVIDENCE RETRIEVAL TEST: PASSED")

except Exception as error:
    print("\nEVIDENCE RETRIEVAL TEST: FAILED")
    print("Error:", error)

finally:
    db.close()
