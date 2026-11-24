
import pytest

from backend.app.models.user import User
from backend.app.models.workspace import Workspace
from backend.app.models.document import Document
from backend.app.models.document_version import DocumentVersion
from backend.app.models.document_segment import DocumentSegment
from backend.app.models.document_embedding import DocumentEmbedding

import backend.app.services.embedding_service as embedding_service


@pytest.fixture
def embedding_test_segments(test_db):
    """Create two isolated document segments for embedding tests."""

    owner = User(
        full_name="Embedding Test Owner",
        email="embedding-owner@example.com",
        hashed_password="test-hash",
        is_active=True,
    )
    test_db.add(owner)
    test_db.commit()

    workspace = Workspace(
        name="Embedding Test Workspace",
        description="Workspace for embedding tests",
        owner_id=owner.id,
    )
    test_db.add(workspace)
    test_db.commit()

    document = Document(
        workspace_id=workspace.id,
        uploaded_by_id=owner.id,
        original_filename="embedding_test.txt",
        stored_filename="embedding_test.txt",
        file_type="txt",
        file_size=100,
        status="processed",
        extracted_text="Test document content.",
    )
    test_db.add(document)
    test_db.commit()

    version = DocumentVersion(
        document_id=document.id,
        version_number=1,
        checksum="a" * 64,
        storage_path="embedding_test.txt",
        is_current=True,
    )
    test_db.add(version)
    test_db.commit()

    segments = [
        DocumentSegment(
            document_version_id=version.id,
            segment_index=0,
            segment_type="text",
            section_title="Application Rules",
            content="Employees must submit applications before the deadline.",
        ),
        DocumentSegment(
            document_version_id=version.id,
            segment_index=1,
            segment_type="text",
            section_title="Approval Rules",
            content="Managers are responsible for approving applications.",
        ),
    ]

    test_db.add_all(segments)
    test_db.commit()

    for segment in segments:
        test_db.refresh(segment)

    return segments


def test_save_segment_embeddings_successfully(
    test_db,
    embedding_test_segments,
    monkeypatch,
):
    segments = embedding_test_segments

    fake_vectors = [
        [0.1] * 384,
        [0.2] * 384,
    ]

    monkeypatch.setattr(
        embedding_service,
        "generate_embeddings",
        lambda texts: fake_vectors,
    )

    saved = embedding_service.save_segment_embeddings(
        test_db,
        segments,
    )

    test_db.commit()

    assert len(saved) == 2

    records = (
        test_db.query(DocumentEmbedding)
        .order_by(DocumentEmbedding.segment_id)
        .all()
    )

    assert len(records) == 2

    for record in records:
        assert record.model_name == embedding_service.EMBEDDING_MODEL_NAME
        assert record.dimensions == 384
        assert len(record.embedding) == 384


def test_duplicate_embeddings_are_not_created(
    test_db,
    embedding_test_segments,
    monkeypatch,
):
    segments = embedding_test_segments

    fake_vectors = [
        [0.1] * 384,
        [0.2] * 384,
    ]

    monkeypatch.setattr(
        embedding_service,
        "generate_embeddings",
        lambda texts: fake_vectors,
    )

    first_result = embedding_service.save_segment_embeddings(
        test_db,
        segments,
    )
    test_db.commit()

    second_result = embedding_service.save_segment_embeddings(
        test_db,
        segments,
    )
    test_db.commit()

    assert len(first_result) == 2
    assert len(second_result) == 0

    count = test_db.query(DocumentEmbedding).count()

    assert count == 2


def test_different_model_embedding_does_not_block_current_model(
    test_db,
    embedding_test_segments,
    monkeypatch,
):
    segment = embedding_test_segments[0]

    other_model_record = DocumentEmbedding(
        segment_id=segment.id,
        model_name="another-test-model",
        dimensions=384,
        embedding=[0.3] * 384,
    )

    test_db.add(other_model_record)
    test_db.commit()

    monkeypatch.setattr(
        embedding_service,
        "generate_embeddings",
        lambda texts: [[0.5] * 384 for _ in texts],
    )

    saved = embedding_service.save_segment_embeddings(
        test_db,
        [segment],
    )
    test_db.commit()

    assert len(saved) == 1

    records = (
        test_db.query(DocumentEmbedding)
        .filter(DocumentEmbedding.segment_id == segment.id)
        .all()
    )

    assert len(records) == 2

    model_names = {record.model_name for record in records}

    assert "another-test-model" in model_names
    assert embedding_service.EMBEDDING_MODEL_NAME in model_names
