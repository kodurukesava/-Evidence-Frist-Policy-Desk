import pytest

from sqlalchemy import text

from backend.app.models.user import User
from backend.app.models.workspace import Workspace
from backend.app.models.document import Document
from backend.app.models.document_version import DocumentVersion
from backend.app.models.document_segment import DocumentSegment
from backend.app.services.auth_service import create_access_token
from backend.app.services.document_search import search_document_segments


def auth_headers(user_id):
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def document_search_data(test_db):
    """Create isolated workspaces with current and outdated documents."""

    owner = User(
        full_name="Search Owner",
        email="search-owner@example.com",
        hashed_password="test-hash",
        is_active=True,
    )

    other_owner = User(
        full_name="Other Owner",
        email="other-owner@example.com",
        hashed_password="test-hash",
        is_active=True,
    )

    viewer = User(
        full_name="Search Viewer",
        email="search-viewer@example.com",
        hashed_password="test-hash",
        is_active=True,
    )

    outsider = User(
        full_name="Search Outsider",
        email="search-outsider@example.com",
        hashed_password="test-hash",
        is_active=True,
    )

    test_db.add_all([owner, other_owner, viewer, outsider])
    test_db.commit()

    workspace_one = Workspace(
        name="Workspace One",
        description="First test workspace",
        owner_id=owner.id,
    )

    workspace_two = Workspace(
        name="Workspace Two",
        description="Second test workspace",
        owner_id=other_owner.id,
    )

    test_db.add_all([workspace_one, workspace_two])
    test_db.commit()

    # Viewer is allowed to search Workspace One.
    from backend.app.models.membership import WorkspaceMembership

    membership = WorkspaceMembership(
        workspace_id=workspace_one.id,
        user_id=viewer.id,
        role="viewer",
    )

    test_db.add(membership)
    test_db.commit()

    document_one = Document(
        workspace_id=workspace_one.id,
        uploaded_by_id=owner.id,
        original_filename="policy_one.txt",
        stored_filename="policy_one.txt",
        file_type="txt",
        file_size=100,
        status="processed",
        extracted_text="Shared searchable policy content",
    )

    document_two = Document(
        workspace_id=workspace_two.id,
        uploaded_by_id=other_owner.id,
        original_filename="policy_two.txt",
        stored_filename="policy_two.txt",
        file_type="txt",
        file_size=100,
        status="processed",
        extracted_text="Shared searchable policy content",
    )

    test_db.add_all([document_one, document_two])
    test_db.commit()

    old_version = DocumentVersion(
        document_id=document_one.id,
        version_number=1,
        storage_path="test/old-version.txt",
        is_current=False,
    )

    current_version = DocumentVersion(
        document_id=document_one.id,
        version_number=2,
        storage_path="test/current-version.txt",
        is_current=True,
    )

    other_workspace_version = DocumentVersion(
        document_id=document_two.id,
        version_number=1,
        storage_path="test/other-workspace.txt",
        is_current=True,
    )

    test_db.add_all([
        old_version,
        current_version,
        other_workspace_version,
    ])
    test_db.commit()

    segments = [
        DocumentSegment(
            document_version_id=old_version.id,
            segment_index=0,
            content="Shared searchable policy content from old version",
        ),
        DocumentSegment(
            document_version_id=current_version.id,
            segment_index=0,
            content="Shared searchable policy content from current version",
        ),
        DocumentSegment(
            document_version_id=other_workspace_version.id,
            segment_index=0,
            content="Shared searchable policy content from another workspace",
        ),
    ]

    test_db.add_all(segments)
    test_db.commit()

    # Initialize FTS5 inside the isolated test database.
    connection = test_db.connection()

    connection.exec_driver_sql("""
        CREATE VIRTUAL TABLE document_segments_fts
        USING fts5(
            content,
            content='document_segments',
            content_rowid='id',
            tokenize='unicode61'
        )
    """)

    connection.exec_driver_sql("""
        INSERT INTO document_segments_fts(document_segments_fts)
        VALUES ('rebuild')
    """)

    return {
        "owner": owner,
        "other_owner": other_owner,
        "viewer": viewer,
        "outsider": outsider,
        "workspace_one": workspace_one,
        "workspace_two": workspace_two,
        "document_one": document_one,
        "document_two": document_two,
        "old_version": old_version,
        "current_version": current_version,
    }


def test_search_returns_only_documents_from_requested_workspace(
    test_db,
    document_search_data,
):
    workspace_id = document_search_data["workspace_one"].id

    results = search_document_segments(
        db=test_db,
        workspace_id=workspace_id,
        query="Shared searchable policy",
    )

    assert len(results) == 1
    assert results[0]["workspace_id"] == workspace_id
    assert (
        results[0]["document_id"]
        == document_search_data["document_one"].id
    )


def test_search_excludes_outdated_document_versions(
    test_db,
    document_search_data,
):
    workspace_id = document_search_data["workspace_one"].id

    results = search_document_segments(
        db=test_db,
        workspace_id=workspace_id,
        query="Shared searchable policy",
    )

    returned_version_ids = {
        result["version_id"] for result in results
    }

    assert (
        document_search_data["current_version"].id
        in returned_version_ids
    )

    assert (
        document_search_data["old_version"].id
        not in returned_version_ids
    )


def test_viewer_can_search_accessible_workspace(
    client,
    document_search_data,
):
    viewer = document_search_data["viewer"]
    workspace_id = document_search_data["workspace_one"].id

    response = client.get(
        f"/documents/search/{workspace_id}",
        params={"query": "Shared searchable policy"},
        headers=auth_headers(viewer.id),
    )

    assert response.status_code == 200
    assert response.json()["workspace_id"] == workspace_id
    assert response.json()["total_results"] == 1


def test_non_member_cannot_search_another_workspace(
    client,
    document_search_data,
):
    outsider = document_search_data["outsider"]
    workspace_id = document_search_data["workspace_one"].id

    response = client.get(
        f"/documents/search/{workspace_id}",
        params={"query": "Shared searchable policy"},
        headers=auth_headers(outsider.id),
    )

    assert response.status_code == 404


def test_search_rejects_empty_query(
    client,
    document_search_data,
):
    owner = document_search_data["owner"]
    workspace_id = document_search_data["workspace_one"].id

    response = client.get(
        f"/documents/search/{workspace_id}",
        params={"query": "   "},
        headers=auth_headers(owner.id),
    )

    assert response.status_code == 400


@pytest.mark.parametrize("limit", [0, 51])
def test_search_rejects_invalid_result_limit(
    client,
    document_search_data,
    limit,
):
    owner = document_search_data["owner"]
    workspace_id = document_search_data["workspace_one"].id

    response = client.get(
        f"/documents/search/{workspace_id}",
        params={
            "query": "Shared searchable policy",
            "limit": limit,
        },
        headers=auth_headers(owner.id),
    )

    assert response.status_code == 400


def test_search_service_rejects_query_without_searchable_words(
    test_db,
):
    with pytest.raises(ValueError):
        search_document_segments(
            db=test_db,
            workspace_id=1,
            query="!!!",
        )
def test_viewer_cannot_upload_document(
    client,
    document_search_data,
):
    viewer = document_search_data["viewer"]
    workspace_id = document_search_data["workspace_one"].id

    response = client.post(
        f"/documents/upload/{workspace_id}",
        headers=auth_headers(viewer.id),
        files={
            "file": (
                "viewer_upload.txt",
                b"Test document content",
                "text/plain",
            )
        },
    )

    assert response.status_code == 404


def test_non_member_cannot_upload_document(
    client,
    document_search_data,
):
    outsider = document_search_data["outsider"]
    workspace_id = document_search_data["workspace_one"].id

    response = client.post(
        f"/documents/upload/{workspace_id}",
        headers=auth_headers(outsider.id),
        files={
            "file": (
                "outsider_upload.txt",
                b"Unauthorized document content",
                "text/plain",
            )
        },
    )

    assert response.status_code == 404

def test_exact_phrase_match_ranks_before_separate_term_matches(
    test_db,
    document_search_data,
):
    data = document_search_data

    exact_phrase_segment = DocumentSegment(
        document_version_id=data["current_version"].id,
        segment_index=1,
        content=(
            "The employee leave policy explains "
            "annual leave eligibility and procedures."
        ),
    )

    separate_terms_segment = DocumentSegment(
        document_version_id=data["current_version"].id,
        segment_index=2,
        content=(
            "The employee handbook explains leave eligibility "
            "and the policy requirements."
        ),
    )

    test_db.add_all([
        exact_phrase_segment,
        separate_terms_segment,
    ])
    test_db.commit()

    # Rebuild FTS because this test inserts segments after fixture setup.
    connection = test_db.connection()

    connection.exec_driver_sql("""
        INSERT INTO document_segments_fts(document_segments_fts)
        VALUES ('rebuild')
    """)

    results = search_document_segments(
        db=test_db,
        workspace_id=data["workspace_one"].id,
        query="employee leave policy",
    )

    assert len(results) == 2

    # Exact phrase must appear before the separate-term match.
    assert results[0]["segment_id"] == exact_phrase_segment.id
    assert results[1]["segment_id"] == separate_terms_segment.id
def test_search_rejects_query_longer_than_500_characters(
    client,
    document_search_data,
):
    owner = document_search_data["owner"]
    workspace_id = document_search_data["workspace_one"].id

    long_query = "a" * 501

    response = client.get(
        f"/documents/search/{workspace_id}",
        params={"query": long_query},
        headers=auth_headers(owner.id),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Search query cannot exceed 500 characters."
    )