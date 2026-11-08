
from backend.app.services.claim_support_validator import validate_claim_support


evidence = [
    {
        "evidence_id": "DOC-1-VER-1-SEG-1",
        "content": (
            "Employees must inform their manager "
            "when taking leave."
        ),
    }
]


# TEST 1: Supported claim
supported_result = validate_claim_support(
    claims=[
        "Employees inform their manager when taking leave."
    ],
    retrieved_evidence=evidence,
)

assert supported_result["is_fully_supported"] is True
assert len(supported_result["supported_claims"]) == 1

print("TEST 1 PASSED: Supported claim accepted.")


# TEST 2: Unsupported claim
unsupported_result = validate_claim_support(
    claims=[
        "Employees receive 90 days of maternity leave."
    ],
    retrieved_evidence=evidence,
)

assert unsupported_result["is_fully_supported"] is False
assert len(unsupported_result["unsupported_claims"]) == 1

print("TEST 2 PASSED: Unsupported claim rejected.")


# TEST 3: Mixed claims
mixed_result = validate_claim_support(
    claims=[
        "Employees inform their manager when taking leave.",
        "Employees receive 90 days of maternity leave.",
    ],
    retrieved_evidence=evidence,
)

assert mixed_result["is_fully_supported"] is False
assert len(mixed_result["supported_claims"]) == 1
assert len(mixed_result["unsupported_claims"]) == 1

print("TEST 3 PASSED: Mixed claims correctly classified.")


print("\nCLAIM SUPPORT VALIDATION TESTS PASSED")
