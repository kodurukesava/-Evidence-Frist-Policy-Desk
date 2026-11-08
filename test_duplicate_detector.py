
from backend.app.services.duplicate_detector import (
    detect_duplicate_evidence,
)


evidence = [
    {
        "evidence_id": "DOC-7-VER-1-SEG-1",
        "content": "Employees must inform their manager when taking leave.",
    },
    {
        "evidence_id": "DOC-8-VER-2-SEG-2",
        "content": "  Employees must inform their manager when taking leave.  ",
    },
    {
        "evidence_id": "DOC-9-VER-1-SEG-1",
        "content": "Employees must arrive at work on time.",
    },
]


result = detect_duplicate_evidence(evidence)

print("\nDUPLICATE EVIDENCE DETECTION TEST")
print("================================")

print("Total evidence:", result["total_evidence"])
print("Unique evidence:", result["unique_count"])
print("Duplicate evidence:", result["duplicate_count"])

print("\nDuplicate groups:")
for group in result["duplicate_groups"]:
    print(group)

assert result["total_evidence"] == 3
assert result["unique_count"] == 2
assert result["duplicate_count"] == 1

assert len(result["duplicate_groups"]) == 1

assert result["duplicate_groups"][0]["primary_evidence_id"] == (
    "DOC-7-VER-1-SEG-1"
)

assert result["duplicate_groups"][0]["duplicate_evidence_ids"] == [
    "DOC-8-VER-2-SEG-2"
]

print("\nDUPLICATE DETECTION TEST: PASSED")
