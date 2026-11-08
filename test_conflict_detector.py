from backend.app.services.conflict_detector import detect_conflicts


def create_evidence(evidence_id, document_id, content):
    return {
        "evidence_id": evidence_id,
        "document_id": document_id,
        "document_name": f"policy_{document_id}.txt",
        "content": content,
    }


def test_detect_opposing_permission_rules():

    evidence = [
        create_evidence(
            "DOC-1-VER-1-SEG-1",
            1,
            "Employees may carry forward unused leave days."
        ),
        create_evidence(
            "DOC-2-VER-1-SEG-1",
            2,
            "Employees cannot carry forward unused leave days."
        ),
    ]

    result = detect_conflicts(evidence)

    assert result["potential_conflict_count"] == 1
    assert result["conflicts"][0]["status"] == "potential_conflict"


def test_no_conflict_for_same_policy_rule():

    evidence = [
        create_evidence(
            "DOC-1-VER-1-SEG-1",
            1,
            "Employees may carry forward unused leave days."
        ),
        create_evidence(
            "DOC-2-VER-1-SEG-1",
            2,
            "Employees may carry forward unused leave days."
        ),
    ]

    result = detect_conflicts(evidence)

    assert result["potential_conflict_count"] == 0


def test_unrelated_topics_should_not_conflict():

    evidence = [
        create_evidence(
            "DOC-1-VER-1-SEG-1",
            1,
            "Employees may carry forward unused leave days."
        ),
        create_evidence(
            "DOC-2-VER-1-SEG-1",
            2,
            "Employees must submit their travel expenses monthly."
        ),
    ]

    result = detect_conflicts(evidence)

    assert result["potential_conflict_count"] == 0


def test_empty_evidence():

    result = detect_conflicts([])

    assert result["total_evidence_compared"] == 0
    assert result["potential_conflict_count"] == 0
    assert result["conflicts"] == []


if __name__ == "__main__":
    test_detect_opposing_permission_rules()
    test_no_conflict_for_same_policy_rule()
    test_unrelated_topics_should_not_conflict()
    test_empty_evidence()

    print("All conflict detector tests passed!")