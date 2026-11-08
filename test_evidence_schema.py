from backend.app.schemas.evidence import (
    EvidenceItem,
    EvidenceResponse,
)

print("\n========== EVIDENCE SCHEMA TEST ==========")

evidence = EvidenceItem(
    evidence_id="DOC-7-VER-1-SEG-1",
    document_id=7,
    document_name="sample.txt",
    workspace_id=1,
    version_id=1,
    segment_id=1,
    segment_index=1,
    section_title=None,
    content="Employees must arrive at work on time.",
    relevance_score=-1.5,
)

response = EvidenceResponse(
    query="What is the attendance policy?",
    workspace_id=1,
    answer="Employees must arrive at work on time.",
    status="supported",
    evidence=[evidence],
    citations=["DOC-7-VER-1-SEG-1"],
    citations_valid=True,
)

print("\nEvidence ID:", response.evidence[0].evidence_id)
print("Answer:", response.answer)
print("Status:", response.status)
print("Citations:", response.citations)
print("Citation validation:", response.citations_valid)

print("\nEVIDENCE SCHEMA TEST: PASSED")