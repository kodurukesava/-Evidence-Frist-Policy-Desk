
def validate_citations(
    answer_citations: list[str],
    retrieved_evidence: list[dict],
):
    """
    Validate whether every citation in an answer
    refers to an evidence item retrieved by the system.
    """

    valid_evidence_ids = {
        item["evidence_id"]
        for item in retrieved_evidence
    }

    valid_citations = []
    invalid_citations = []

    for citation in answer_citations:
        if citation in valid_evidence_ids:
            valid_citations.append(citation)
        else:
            invalid_citations.append(citation)

    return {
        "is_valid": len(invalid_citations) == 0,
        "valid_citations": valid_citations,
        "invalid_citations": invalid_citations,
        "total_citations": len(answer_citations),
    }
