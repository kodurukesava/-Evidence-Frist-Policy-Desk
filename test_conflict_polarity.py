
from backend.app.services.conflict_detector import detect_polarity


def test_may_not_is_negative():
    result = detect_polarity(
        "Employees may not carry forward unused leave."
    )
    assert result == ("permission", "negative")


def test_must_not_is_negative():
    result = detect_polarity(
        "Employees must not share confidential information."
    )
    assert result == ("obligation", "negative")


def test_may_is_positive():
    result = detect_polarity(
        "Employees may carry forward unused leave."
    )
    assert result == ("permission", "positive")


def test_must_is_positive():
    result = detect_polarity(
        "Employees must submit their reports."
    )
    assert result == ("obligation", "positive")


def test_mixed_permission_statement_is_ambiguous():
    result = detect_polarity(
        "Employees may carry leave forward but may not carry it forward."
    )
    assert result == (None, None)


def test_mixed_policy_categories_are_ambiguous():
    result = detect_polarity(
        "Employees must submit reports, but sharing them is optional."
    )
    assert result == (None, None)


if __name__ == "__main__":
    test_may_not_is_negative()
    test_must_not_is_negative()
    test_may_is_positive()
    test_must_is_positive()
    test_mixed_permission_statement_is_ambiguous()
    test_mixed_policy_categories_are_ambiguous()

    print("All polarity regression tests passed!")
