
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
def lifecycle_test_data(test_db, tmp_path, monkeypatch):
    """Create an isolated workspace, users, document, and initial version."""

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
        full_name="Lifecycle Owner",
        email="lifecycle-owner@example.com",
        hashed_password="test-hash",
        is_active=True,
    )

    admin = User(
        full_name="Lifecycle Admin",
        email="lifecycle-admin@example.com",
        hashed_password="test-hash",
        is_active=True,
    )

    viewer = User(
        full_name="Lifecycle Viewer",
        email="lifecycle-viewer@example.com",
        hashed_password="test-hash",
        is_active=True,
    )

    outsider = User(
        full_name="Lifecycle Outsider",
        email="lifecycle-outsider@example.com",
        hashed_password="test-hash",
        is_active=True,
    )

    test_db.add_all([owner, admin, viewer, outsider])
    test_db.commit()

    workspace = Workspace(
        name="Lifecycle Test Workspace",
        description="Workspace for lifecycle tests",
        owner_id=owner.id,
    )

    test_db.add(workspace)
    test_db.commit()

    memberships = [
        WorkspaceMembership(
            workspace_id=workspace.id,
            user_id=admin.id,
            role="admin",
        ),
        WorkspaceMembership(
            workspace_id=workspace.id,
            user_id=viewer.id,
            role="viewer",
        ),
    ]

    test_db.add_all(memberships)
    test_db.commit()

    original_content = (
        b"Original policy document. This document contains "
        b"important policy rules and administrative requirements."
    )

    original_filename = "lifecycle_policy.txt"
    stored_filename = "lifecycle-original.txt"

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
        "admin": admin,
        "viewer": viewer,
        "outsider": outsider,
        "workspace": workspace,
        "document": document,
        "initial_version": initial_version,
        "original_path": original_path,
        "storage_dir": tmp_path,
    }


def test_owner_can_archive_document(
    client,
    test_db,
    lifecycle_test_data,
):
    data = lifecycle_test_data

    response = client.patch(
        f"/documents/{data['document'].id}/archive",
        headers=auth_headers(data["owner"].id),
    )

    assert response.status_code == 200
    assert response.json()["lifecycle_status"] == "archived"

    test_db.refresh(data["document"])

    assert data["document"].lifecycle_status == "archived"
    assert data["document"].archived_at is not None

    # Archiving must preserve the original file.
    assert data["original_path"].exists()


def test_owner_can_restore_archived_document(
    client,
    test_db,
    lifecycle_test_data,
):
    data = lifecycle_test_data

    archive_response = client.patch(
        f"/documents/{data['document'].id}/archive",
        headers=auth_headers(data["owner"].id),
    )

    assert archive_response.status_code == 200

    restore_response = client.patch(
        f"/documents/{data['document'].id}/restore",
        headers=auth_headers(data["owner"].id),
    )

    assert restore_response.status_code == 200
    assert restore_response.json()["lifecycle_status"] == "active"

    test_db.refresh(data["document"])

    assert data["document"].lifecycle_status == "active"
    assert data["document"].archived_at is None

    # Restoring must preserve the original file.
    assert data["original_path"].exists()


def test_owner_can_soft_delete_document_without_removing_data(
    client,
    test_db,
    lifecycle_test_data,
):
    data = lifecycle_test_data

    response = client.delete(
        f"/documents/{data['document'].id}",
        headers=auth_headers(data["owner"].id),
    )

    assert response.status_code == 200
    assert response.json()["lifecycle_status"] == "deleted"

    test_db.refresh(data["document"])

    assert data["document"].lifecycle_status == "deleted"
    assert data["document"].deleted_at is not None

    # The document database record must remain.
    stored_document = test_db.query(Document).filter(
        Document.id == data["document"].id
    ).first()

    assert stored_document is not None

    # The original file must remain.
    assert data["original_path"].exists()

    # The document version record must remain.
    versions = test_db.query(DocumentVersion).filter(
        DocumentVersion.document_id == data["document"].id
    ).all()

    assert len(versions) == 1
    assert versions[0].version_number == 1


def test_admin_can_archive_document(
    client,
    test_db,
    lifecycle_test_data,
):
    data = lifecycle_test_data

    response = client.patch(
        f"/documents/{data['document'].id}/archive",
        headers=auth_headers(data["admin"].id),
    )

    assert response.status_code == 200

    test_db.refresh(data["document"])

    assert data["document"].lifecycle_status == "archived"


@pytest.mark.parametrize("user_key", ["viewer", "outsider"])
def test_unauthorized_users_cannot_archive_document(
    client,
    lifecycle_test_data,
    user_key,
):
    data = lifecycle_test_data
    user = data[user_key]

    response = client.patch(
        f"/documents/{data['document'].id}/archive",
        headers=auth_headers(user.id),
    )

    assert response.status_code == 404


def test_deleted_document_cannot_be_restored(
    client,
    lifecycle_test_data,
):
    data = lifecycle_test_data

    delete_response = client.delete(
        f"/documents/{data['document'].id}",
        headers=auth_headers(data["owner"].id),
    )

    assert delete_response.status_code == 200

    restore_response = client.patch(
        f"/documents/{data['document'].id}/restore",
        headers=auth_headers(data["owner"].id),
    )

    assert restore_response.status_code == 409


def test_archived_document_cannot_receive_new_version(
    client,
    test_db,
    lifecycle_test_data,
):
    data = lifecycle_test_data

    archive_response = client.patch(
        f"/documents/{data['document'].id}/archive",
        headers=auth_headers(data["owner"].id),
    )

    assert archive_response.status_code == 200

    response = client.post(
        f"/documents/{data['document'].id}/versions",
        headers=auth_headers(data["owner"].id),
        files={
            "file": (
                "updated_policy.txt",
                b"Updated policy content that must not be uploaded.",
                "text/plain",
            )
        },
    )

    assert response.status_code == 409

    # No additional version should be created.
    versions = test_db.query(DocumentVersion).filter(
        DocumentVersion.document_id == data["document"].id
    ).all()

    assert len(versions) == 1


def test_already_archived_document_cannot_be_archived_again(
    client,
    lifecycle_test_data,
):
    data = lifecycle_test_data

    first_response = client.patch(
        f"/documents/{data['document'].id}/archive",
        headers=auth_headers(data["owner"].id),
    )

    assert first_response.status_code == 200

    second_response = client.patch(
        f"/documents/{data['document'].id}/archive",
        headers=auth_headers(data["owner"].id),
    )

    assert second_response.status_code == 409
