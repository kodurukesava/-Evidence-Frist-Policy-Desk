
import re


def validate_claim_support(
    claims: list[str],
    retrieved_evidence: list[dict],
):
    """
    Check whether individual answer claims have textual support
    in the retrieved evidence passages.

    This is a conservative lexical check, not a semantic
    entailment guarantee.
    """

    supported_claims = []
    unsupported_claims = []

    evidence_text = " ".join(
        item.get("content", "")
        for item in retrieved_evidence
    ).lower()

    def normalize(text: str) -> set[str]:
        words = re.findall(r"\b[a-z0-9]+\b", text.lower())

        stop_words = {
            "the", "a", "an", "is", "are", "was", "were",
            "to", "of", "in", "on", "for", "and", "or",
            "must", "should", "can", "could", "would",
            "be", "do", "does", "did", "has", "have",
        }

        return {
            word for word in words
            if word not in stop_words
        }

    evidence_terms = normalize(evidence_text)

    for claim in claims:
        claim_terms = normalize(claim)

        if not claim_terms:
            unsupported_claims.append(claim)
            continue

        overlap = claim_terms.intersection(evidence_terms)

        # Require at least 60% keyword overlap.
        support_ratio = len(overlap) / len(claim_terms)

        if support_ratio >= 0.6:
            supported_claims.append(claim)
        else:
            unsupported_claims.append(claim)

    return {
        "is_fully_supported": len(unsupported_claims) == 0,
        "supported_claims": supported_claims,
        "unsupported_claims": unsupported_claims,
        "total_claims": len(claims),
    }
