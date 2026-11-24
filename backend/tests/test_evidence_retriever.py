
import pytest

import backend.app.services.evidence_retriever as retriever


def test_prepare_search_query_preserves_policy_terms():
    query = "What must employees NOT submit?"

    result = retriever.prepare_search_query(query)

    assert result == "must employees not submit"


def test_prepare_search_query_removes_question_filler():
    query = "What is the application deadline?"

    result = retriever.prepare_search_query(query)

    assert result == "application deadline"


def test_reciprocal_rank_fusion_combines_rankings():
    keyword_results = [
        {"segment_id": 1, "content": "Keyword result"},
        {"segment_id": 2, "content": "Second keyword result"},
    ]

    semantic_results = [
        {"segment_id": 1, "content": "Semantic result"},
        {"segment_id": 3, "content": "Third semantic result"},
    ]

    results = retriever.reciprocal_rank_fusion(
        keyword_results,
        semantic_results,
        limit=10,
    )

    assert [item["segment_id"] for item in results] == [1, 2, 3]

    assert results[0]["keyword_rank"] == 1
    assert results[0]["semantic_rank"] == 1

    assert results[1]["keyword_rank"] == 2
    assert results[1]["semantic_rank"] is None

    assert results[2]["keyword_rank"] is None
    assert results[2]["semantic_rank"] == 2

    assert results[0]["relevance_score"] > results[1]["relevance_score"]
    assert results[0]["relevance_score"] > results[2]["relevance_score"]


def test_reciprocal_rank_fusion_respects_result_limit():
    keyword_results = [
        {"segment_id": 1},
        {"segment_id": 2},
        {"segment_id": 3},
    ]

    results = retriever.reciprocal_rank_fusion(
        keyword_results,
        [],
        limit=2,
    )

    assert len(results) == 2
    assert [item["segment_id"] for item in results] == [1, 2]


def test_hybrid_retrieval_combines_keyword_and_semantic_results(
    monkeypatch,
):
    keyword_results = [
        {
            "segment_id": 1,
            "document_id": 10,
            "document_name": "policy.txt",
            "workspace_id": 5,
            "version_id": 20,
            "segment_index": 1,
            "section_title": "Application Rules",
            "content": "Employees must submit applications.",
            "relevance_score": -2.0,
        }
    ]

    semantic_results = [
        {
            "segment_id": 1,
            "document_id": 10,
            "document_name": "policy.txt",
            "workspace_id": 5,
            "version_id": 20,
            "segment_index": 1,
            "section_title": "Application Rules",
            "content": "Employees must submit applications.",
            "relevance_score": 0.9,
        },
        {
            "segment_id": 2,
            "document_id": 11,
            "document_name": "guidelines.txt",
            "workspace_id": 5,
            "version_id": 21,
            "segment_index": 2,
            "section_title": "Submission Rules",
            "content": "Applications must be submitted before the deadline.",
            "relevance_score": 0.8,
        },
    ]

    calls = {}

    def fake_keyword_search(**kwargs):
        calls["keyword"] = kwargs
        return keyword_results

    def fake_semantic_search(**kwargs):
        calls["semantic"] = kwargs
        return semantic_results

    def fake_deduplication(items):
        return {
            "unique_evidence": items,
            "duplicate_groups": [],
        }

    monkeypatch.setattr(
        retriever,
        "search_document_segments",
        fake_keyword_search,
    )

    monkeypatch.setattr(
        retriever,
        "search_semantic_segments",
        fake_semantic_search,
    )

    monkeypatch.setattr(
        retriever,
        "detect_duplicate_evidence",
        fake_deduplication,
    )

    results = retriever.retrieve_evidence(
        db=None,
        workspace_id=5,
        query="What must employees submit?",
        limit=10,
    )

    assert calls["keyword"]["workspace_id"] == 5
    assert calls["semantic"]["workspace_id"] == 5

    assert calls["keyword"]["query"] == "must employees submit"
    assert calls["semantic"]["query"] == "What must employees submit?"

    assert [item["segment_id"] for item in results] == [1, 2]

    assert results[0]["evidence_id"] == "DOC-10-VER-20-SEG-1"
    assert results[0]["duplicate_source_count"] == 1
    assert results[1]["evidence_id"] == "DOC-11-VER-21-SEG-2"

    assert results[0]["relevance_score"] > results[1]["relevance_score"]


def test_prepare_search_query_rejects_empty_input():
    with pytest.raises(ValueError):
        retriever.prepare_search_query("   ")
