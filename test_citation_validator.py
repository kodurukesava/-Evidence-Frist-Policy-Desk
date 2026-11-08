
from backend.app.database import SessionLocal

from backend.app.services.evidence_retriever import retrieve_evidence
from backend.app.services.citation_validator import validate_citations


db = SessionLocal()

try:
    evidence = retrieve_evidence(
        db=db,
        workspace_id=1,
        query="Attendance Policy",
        limit=10,
    )

    print("\n========== CITATION VALIDATION TEST ==========\n")

    # Test 1: Genuine citation
    valid_id = evidence[0]["evidence_id"]

    valid_result = validate_citations(
        answer_citations=[valid_id],
        retrieved_evidence=evidence,
    )

    print("TEST 1: Genuine Citation")
    print("Citation:", valid_id)
    print("Validation:", valid_result)

    assert valid_result["is_valid"] is True

    # Test 2: Fabricated citation
    invalid_result = validate_citations(
        answer_citations=["DOC-999-VER-999-SEG-999"],
        retrieved_evidence=evidence,
    )

    print("\nTEST 2: Fabricated Citation")
    print("Validation:", invalid_result)

    assert invalid_result["is_valid"] is False
    assert len(invalid_result["invalid_citations"]) == 1

    # Test 3: Mixed citations
    mixed_result = validate_citations(
        answer_citations=[
            evidence[0]["evidence_id"],
            "DOC-999-VER-999-SEG-999",
        ],
        retrieved_evidence=evidence,
    )

    print("\nTEST 3: Mixed Citations")
    print("Validation:", mixed_result)

    assert mixed_result["is_valid"] is False
    assert len(mixed_result["valid_citations"]) == 1
    assert len(mixed_result["invalid_citations"]) == 1

    print("\nCITATION VALIDATION TEST: PASSED")

except Exception as error:
    print("\nCITATION VALIDATION TEST: FAILED")
    print("Error:", error)

finally:
    db.close()
