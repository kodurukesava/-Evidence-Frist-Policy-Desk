
import pytest

from backend.app.models.user import User
from backend.app.models.workspace import Workspace
from backend.app.models.document import Document
from backend.app.models.document_version import DocumentVersion
from backend.app.models.document_segment import DocumentSegment
from backend.app.models.document_embedding import DocumentEmbedding

import backend.app.services.semantic_search as semantic_search
from backend.app.services.embedding_service import EMBEDDING_MODEL_NAME


@pytest.fixture
def semantic_search_data(test_db):
    """Create isolated records for semantic search filtering tests."""

    owner = User(
        full_name="Semantic Test Owner",
        email="semantic-owner@example.com",
        hashed_password="test-hash",
        is_active=True,
    )
    test_db.add(owner)
    test_db.commit()

    workspace = Workspace(
        name="Semantic Test Workspace",
        description="Workspace for semantic search tests",
        owner_id=owner.id,
    )

    other_workspace = Workspace(
        name="Other Semantic Workspace",
        description="Separate workspace",
        owner_id=owner.id,
    )

    test_db.add_all([workspace, other_workspace])
    test_db.commit()

    def create_document(
        workspace_id,
        filename,
        lifecycle_status="active",
    ):
        document = Document(
            workspace_id=workspace_id,
            uploaded_by_id=owner.id,
            original_filename=filename,
            stored_filename=filename,
            file_type="txt",
            file_size=100,
            status="processed",
            lifecycle_status=lifecycle_status,
            extracted_text="Semantic search test content.",
        )
        test_db.add(document)
        test_db.flush()
        return document

    def create_version(document, version_number, is_current):
        version = DocumentVersion(
            document_id=document.id,
            version_number=version_number,
            checksum=str(version_number) * 64,
            storage_path=document.stored_filename,
            is_current=is_current,
        )
        test_db.add(version)
        test_db.flush()
        return version

    def create_segment(version, index, content, vector):
        segment = DocumentSegment(
            document_version_id=version.id,
            segment_index=index,
            segment_type="text",
            section_title="Test Section",
            content=content,
        )
        test_db.add(segment)
        test_db.flush()

        embedding = DocumentEmbedding(
            segment_id=segment.id,
            model_name=EMBEDDING_MODEL_NAME,
            dimensions=384,
            embedding=vector,
        )
        test_db.add(embedding)
        test_db.flush()

        return segment

    matching_vector = [1.0] + [0.0] * 383
    other_vector = [0.0, 1.0] + [0.0] * 382

    # Active document with a current version.
    active_document = create_document(
        workspace.id,
        "active_document.txt",
    )
    current_version = create_version(
        active_document,
        version_number=2,
        is_current=True,
    )
    matching_segment = create_segment(
        current_version,
        1,
        "Employees must submit applications before the deadline.",
        matching_vector,
    )

    # Previous version of the same document.
    old_version = create_version(
        active_document,
        version_number=1,
        is_current=False,
    )
    create_segment(
        old_version,
        1,
        "Old version of the application policy.",
        matching_vector,
    )

    # Archived document in the requested workspace.
    archived_document = create_document(
        workspace.id,
        "archived_document.txt",
        lifecycle_status="archived",
    )
    archived_version = create_version(
        archived_document,
        version_number=1,
        is_current=True,
    )
    create_segment(
        archived_version,
        1,
        "Archived application policy.",
        matching_vector,
    )

    # Active document in another workspace.
    foreign_document = create_document(
        other_workspace.id,
        "foreign_document.txt",
    )
    foreign_version = create_version(
        foreign_document,
        version_number=1,
        is_current=True,
    )
    create_segment(
        foreign_version,
        1,
        "Application policy in another workspace.",
        matching_vector,
    )

    # Another current segment in the requested workspace,
    # but with a lower semantic similarity.
    other_segment = create_segment(
        current_version,
        2,
        "Managers approve employee applications.",
        other_vector,
    )

    test_db.commit()

    return {
        "workspace_id": workspace.id,
        "matching_segment_id": matching_segment.id,
        "other_segment_id": other_segment.id,
    }


def test_cosine_similarity_for_identical_vectors():
    result = semantic_search.cosine_similarity(
        [1.0, 0.0],
        [1.0, 0.0],
    )

    assert result == pytest.approx(1.0)


def test_cosine_similarity_for_orthogonal_vectors():
    result = semantic_search.cosine_similarity(
        [1.0, 0.0],
        [0.0, 1.0],
    )

    assert result == pytest.approx(0.0)


def test_cosine_similarity_for_zero_vector():
    result = semantic_search.cosine_similarity(
        [0.0, 0.0],
        [1.0, 0.0],
    )

    assert result == 0.0


def test_cosine_similarity_rejects_different_dimensions():
    with pytest.raises(ValueError, match="dimensions must match"):
        semantic_search.cosine_similarity(
            [1.0, 0.0],
            [1.0],
        )


def test_semantic_search_respects_workspace_and_document_filters(
    test_db,
    semantic_search_data,
    monkeypatch,
):
    query_vector = [1.0] + [0.0] * 383

    monkeypatch.setattr(
        semantic_search,
        "generate_embeddings",
        lambda texts: [query_vector],
    )

    results = semantic_search.search_semantic_segments(
        db=test_db,
        workspace_id=semantic_search_data["workspace_id"],
        query="Who must submit applications?",
        limit=10,
    )

    returned_segment_ids = {
        result["segment_id"]
        for result in results
    }

    # The matching current, active segment must be returned.
    assert semantic_search_data["matching_segment_id"] in returned_segment_ids

    # The lower-similarity segment is also eligible.
    assert semantic_search_data["other_segment_id"] in returned_segment_ids

    # All results must belong to the requested workspace.
    assert all(
        result["workspace_id"] == semantic_search_data["workspace_id"]
        for result in results
    )

    # The most similar segment must rank first.
    assert results[0]["segment_id"] == (
        semantic_search_data["matching_segment_id"]
    )

    # No old-version, archived, or foreign-workspace segments
    # should appear in the results.
    assert len(results) == 2
