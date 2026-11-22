
from pathlib import Path

import pytest

from backend.app.models.user import User
from backend.app.models.workspace import Workspace
from backend.app.models.membership import WorkspaceMembership
from backend.app.models.document import Document
from backend.app.models.document_version import DocumentVersion
from backend.app.services.auth_service import create_access_token
from backend.app.services.document_segment_service import calculate_file_checksum


def auth_headers(user_id):
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def version_test_data(test_db, tmp_path, monkeypatch):
    """Create an isolated document and its initial version."""

    import backend.app.routes.document as document_route
    import backend.app.services.document_segment_service as segment_service

    monkeypatch.setattr(
        document_route,
        "DOCUMENT_STORAGE_DIR",
        tmp_path,
    )

    monkeypatch.setattr(
        segment_service,
        "DOCUMENT_STORAGE_DIR",
        tmp_path,
    )

    owner = User(
        full_name="Version Owner",
        email="version-owner@example.com",
        hashed_password="test-hash",
        is_active=True,
    )

    viewer = User(
        full_name="Version Viewer",
        email="version-viewer@example.com",
        hashed_password="test-hash",
        is_active=True,
    )

    outsider = User(
        full_name="Version Outsider",
        email="version-outsider@example.com",
        hashed_password="test-hash",
        is_active=True,
    )

    test_db.add_all([owner, viewer, outsider])
    test_db.commit()

    workspace = Workspace(
        name="Version Test Workspace",
        description="Workspace for document version tests",
        owner_id=owner.id,
    )

    test_db.add(workspace)
    test_db.commit()

    membership = WorkspaceMembership(
        workspace_id=workspace.id,
        user_id=viewer.id,
        role="viewer",
    )

    test_db.add(membership)
    test_db.commit()

    original_content = (
        b"Original policy version. This document contains "
        b"the original policy rules and requirements."
    )

    original_filename = "original_policy.txt"
    stored_filename = "original-version.txt"

    original_path = Path(tmp_path) / stored_filename
    original_path.write_bytes(original_content)

    document = Document(
        workspace_id=workspace.id,
        uploaded_by_id=owner.id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_type="txt",
        file_size=len(original_content),
        status="processed",
        extracted_text=original_content.decode("utf-8"),
    )

    test_db.add(document)
    test_db.commit()
    test_db.refresh(document)

    initial_version = DocumentVersion(
        document_id=document.id,
        version_number=1,
        checksum=calculate_file_checksum(original_path),
        storage_path=str(original_path),
        is_current=True,
    )

    test_db.add(initial_version)
    test_db.commit()
    test_db.refresh(initial_version)

    return {
        "owner": owner,
        "viewer": viewer,
        "outsider": outsider,
        "workspace": workspace,
        "document": document,
        "initial_version": initial_version,
        "original_path": original_path,
        "storage_dir": tmp_path,
    }


def test_upload_new_version_successfully(
    client,
    test_db,
    version_test_data,
):
    data = version_test_data

    new_content = (
        b"Updated policy version. This document contains "
        b"the latest policy rules, updated requirements, "
        b"and revised administrative procedures."
    )

    response = client.post(
        f"/documents/{data['document'].id}/versions",
        headers=auth_headers(data["owner"].id),
        files={
            "file": (
                "updated_policy.txt",
                new_content,
                "text/plain",
            )
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["document_id"] == data["document"].id
    assert result["version_number"] == 2
    assert result["is_current"] is True
    assert result["segments_created"] > 0

    versions = (
        test_db.query(DocumentVersion)
        .filter(
            DocumentVersion.document_id == data["document"].id
        )
        .order_by(DocumentVersion.version_number)
        .all()
    )

    assert len(versions) == 2
    assert versions[0].version_number == 1
    assert versions[0].is_current is False
    assert versions[1].version_number == 2
    assert versions[1].is_current is True

    # Previous version file must remain preserved.
    assert data["original_path"].exists()

    # Document metadata must point to the new file.
    test_db.refresh(data["document"])

    assert data["document"].original_filename == "updated_policy.txt"
    assert data["document"].stored_filename != "original-version.txt"


def test_duplicate_upload_does_not_create_another_version(
    client,
    test_db,
    version_test_data,
):
    data = version_test_data

    original_stored_filename = data["document"].stored_filename

    original_files = {
        path.name
        for path in data["storage_dir"].iterdir()
    }

    original_content = data["original_path"].read_bytes()

    response = client.post(
        f"/documents/{data['document'].id}/versions",
        headers=auth_headers(data["owner"].id),
        files={
            "file": (
                "duplicate_policy.txt",
                original_content,
                "text/plain",
            )
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["version_number"] == 1
    assert "already exists" in result["message"]

    versions = (
        test_db.query(DocumentVersion)
        .filter(
            DocumentVersion.document_id == data["document"].id
        )
        .all()
    )

    assert len(versions) == 1
    assert versions[0].is_current is True

    test_db.refresh(data["document"])

    # Duplicate upload must not change document metadata.
    assert (
        data["document"].stored_filename
        == original_stored_filename
    )

    # Duplicate temporary file must be removed.
    remaining_files = {
        path.name
        for path in data["storage_dir"].iterdir()
    }

    assert remaining_files == original_files


def test_viewer_cannot_upload_document_version(
    client,
    version_test_data,
):
    data = version_test_data

    response = client.post(
        f"/documents/{data['document'].id}/versions",
        headers=auth_headers(data["viewer"].id),
        files={
            "file": (
                "viewer_policy.txt",
                b"Unauthorized policy update content.",
                "text/plain",
            )
        },
    )

    assert response.status_code == 404


def test_non_member_cannot_upload_document_version(
    client,
    version_test_data,
):
    data = version_test_data

    response = client.post(
        f"/documents/{data['document'].id}/versions",
        headers=auth_headers(data["outsider"].id),
        files={
            "file": (
                "outsider_policy.txt",
                b"Unauthorized policy update content.",
                "text/plain",
            )
        },
    )

    assert response.status_code == 404


def test_upload_version_for_nonexistent_document_returns_404(
    client,
    version_test_data,
):
    data = version_test_data

    response = client.post(
        "/documents/999999/versions",
        headers=auth_headers(data["owner"].id),
        files={
            "file": (
                "missing_document.txt",
                b"Test content for a missing document.",
                "text/plain",
            )
        },
    )

    assert response.status_code == 404
