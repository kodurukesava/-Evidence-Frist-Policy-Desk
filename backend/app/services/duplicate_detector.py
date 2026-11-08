
import hashlib


def normalize_content(content: str) -> str:
    """Normalize whitespace and letter case for comparison."""
    return " ".join(content.split()).casefold()


def calculate_content_hash(content: str) -> str:
    """Generate a SHA-256 fingerprint for evidence content."""
    normalized = normalize_content(content)

    return hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()


def detect_duplicate_evidence(evidence_items: list[dict]):
    """
    Group identical evidence passages without deleting source records.

    The first occurrence becomes the canonical passage.
    """

    unique_evidence = []
    groups = {}

    for item in evidence_items:
        content = item.get("content", "")

        if not content.strip():
            unique_evidence.append(item)
            continue

        content_hash = calculate_content_hash(content)

        if content_hash not in groups:
            groups[content_hash] = {
                "content_hash": content_hash,
                "primary_evidence_id": item["evidence_id"],
                "duplicate_evidence_ids": [],
                "source_count": 1,
            }

            unique_evidence.append(item)

        else:
            groups[content_hash]["duplicate_evidence_ids"].append(
                item["evidence_id"]
            )

            groups[content_hash]["source_count"] += 1

    duplicate_groups = [
        group
        for group in groups.values()
        if group["source_count"] > 1
    ]

    return {
        "unique_evidence": unique_evidence,
        "duplicate_groups": duplicate_groups,
        "total_evidence": len(evidence_items),
        "unique_count": len(unique_evidence),
        "duplicate_count": (
            len(evidence_items) - len(unique_evidence)
        ),
    }
