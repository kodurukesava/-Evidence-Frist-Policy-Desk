
import re
from itertools import combinations


STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were",
    "to", "of", "in", "on", "for", "and", "or",
    "by", "with", "from", "that", "this", "these",
    "those", "it", "its", "be", "been", "being",
    "employee", "employees", "company", "policy",
}


# Opposing policy expressions.
POLARITY_PATTERNS = {
    "permission": {
        "positive": [
            r"\bmay\b",
            r"\bcan\b",
            r"\ballowed\b",
            r"\bpermitted\b",
        ],
        "negative": [
            r"\bmay not\b",
            r"\bcannot\b",
            r"\bcan't\b",
            r"\bnot allowed\b",
            r"\bnot permitted\b",
            r"\bprohibited\b",
            r"\bforbidden\b",
        ],
    },
    "obligation": {
        "positive": [
            r"\bmust\b",
            r"\bshall\b",
            r"\brequired\b",
            r"\bmandatory\b",
        ],
        "negative": [
            r"\bmust not\b",
            r"\bshall not\b",
            r"\bnot required\b",
            r"\boptional\b",
        ],
    },
}


def normalize_text(text: str) -> str:
    """Normalize text for consistent comparison."""

    return re.sub(
        r"\s+",
        " ",
        text.casefold()
    ).strip()


def extract_topic_terms(text: str) -> set[str]:
    """Extract meaningful words while excluding common terms."""

    words = re.findall(
        r"\b[a-z0-9]+\b",
        normalize_text(text)
    )

    return {
        word
        for word in words
        if word not in STOP_WORDS
    }


def detect_polarity(text: str):
    """Identify positive or negative policy expressions safely."""

    normalized = normalize_text(text)
    detected_categories = []

    for category, expressions in POLARITY_PATTERNS.items():

        negative_found = any(
            re.search(pattern, normalized)
            for pattern in expressions["negative"]
        )

        # Remove negative expressions before checking positive ones.
        # This prevents "may not" from also matching "may".
        positive_text = normalized

        for pattern in expressions["negative"]:
            positive_text = re.sub(
                pattern,
                " ",
                positive_text
            )

        positive_found = any(
            re.search(pattern, positive_text)
            for pattern in expressions["positive"]
        )

        # If both forms occur in one passage, treat it as ambiguous.
        if positive_found and negative_found:
            continue

        if positive_found:
            detected_categories.append((category, "positive"))

        elif negative_found:
            detected_categories.append((category, "negative"))

    # Avoid guessing if multiple categories are detected.
    if len(detected_categories) == 1:
        return detected_categories[0]

    return None, None


def detect_conflicts(evidence_items: list[dict]) -> dict:
    """
    Identify potential contradictions between evidence passages.

    This is a rule-based screening method, not a guarantee
    of semantic contradiction.
    """

    potential_conflicts = []

    for first, second in combinations(evidence_items, 2):

        # Do not compare a passage against itself.
        if first["evidence_id"] == second["evidence_id"]:
            continue

        first_category, first_polarity = detect_polarity(
            first["content"]
        )

        second_category, second_polarity = detect_polarity(
            second["content"]
        )

        # Both statements must contain opposing expressions
        # from the same policy category.
        if (
            first_category is None
            or first_category != second_category
            or first_polarity == second_polarity
        ):
            continue

        first_terms = extract_topic_terms(first["content"])
        second_terms = extract_topic_terms(second["content"])

        shared_terms = first_terms.intersection(second_terms)

        if not first_terms or not second_terms:
            continue

        # Compare the shared topic against the smaller passage.
        topic_overlap = (
            len(shared_terms) / min(
                len(first_terms),
                len(second_terms)
            )
        )

        # Require meaningful topic overlap.
        if topic_overlap < 0.5:
            continue

        potential_conflicts.append({
            "conflict_type": second_category,
            "status": "potential_conflict",
            "evidence_a": {
                "evidence_id": first["evidence_id"],
                "document_id": first["document_id"],
                "document_name": first["document_name"],
                "content": first["content"],
            },
            "evidence_b": {
                "evidence_id": second["evidence_id"],
                "document_id": second["document_id"],
                "document_name": second["document_name"],
                "content": second["content"],
            },
            "shared_terms": sorted(shared_terms),
            "topic_overlap": round(topic_overlap, 2),
        })

    return {
        "total_evidence_compared": len(evidence_items),
        "potential_conflict_count": len(potential_conflicts),
        "conflicts": potential_conflicts,
    }
