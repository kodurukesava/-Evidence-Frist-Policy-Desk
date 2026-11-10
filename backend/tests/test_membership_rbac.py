
import pytest

from backend.app.models.user import User
from backend.app.models.workspace import Workspace
from backend.app.models.membership import WorkspaceMembership
from backend.app.services.auth_service import create_access_token


def auth_headers(user_id):
    """Create authentication headers for a test user."""
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def rbac_data(test_db):
    """Create owner, admin, editor, viewer and target users."""
    owner = User(
        full_name="Workspace Owner",
        email="owner@example.com",
        hashed_password="test-hash",
        is_active=True,
    )

    admin = User(
        full_name="Workspace Admin",
        email="admin@example.com",
        hashed_password="test-hash",
        is_active=True,
    )

    editor = User(
        full_name="Workspace Editor",
        email="editor@example.com",
        hashed_password="test-hash",
        is_active=True,
    )

    viewer = User(
        full_name="Workspace Viewer",
        email="viewer@example.com",
        hashed_password="test-hash",
        is_active=True,
    )

    target = User(
        full_name="Target User",
        email="target@example.com",
        hashed_password="test-hash",
        is_active=True,
    )

    admin_target = User(
        full_name="Another Admin",
        email="another-admin@example.com",
        hashed_password="test-hash",
        is_active=True,
    )

    test_db.add_all([
        owner, admin, editor, viewer, target, admin_target
    ])
    test_db.commit()

    workspace = Workspace(
        name="RBAC Test Workspace",
        description="Isolated workspace for permission tests",
        owner_id=owner.id,
    )

    test_db.add(workspace)
    test_db.commit()
    test_db.refresh(workspace)

    memberships = [
        WorkspaceMembership(
            workspace_id=workspace.id,
            user_id=admin.id,
            role="admin",
        ),
        WorkspaceMembership(
            workspace_id=workspace.id,
            user_id=editor.id,
            role="editor",
        ),
        WorkspaceMembership(
            workspace_id=workspace.id,
            user_id=viewer.id,
            role="viewer",
        ),
        WorkspaceMembership(
            workspace_id=workspace.id,
            user_id=admin_target.id,
            role="admin",
        ),
    ]

    test_db.add_all(memberships)
    test_db.commit()

    return {
        "workspace": workspace,
        "owner": owner,
        "admin": admin,
        "editor": editor,
        "viewer": viewer,
        "target": target,
        "admin_target": admin_target,
    }


def test_owner_can_add_update_and_remove_admin(client, rbac_data):
    workspace_id = rbac_data["workspace"].id
    owner_headers = auth_headers(rbac_data["owner"].id)
    target_id = rbac_data["target"].id

    # Owner can assign the admin role.
    response = client.post(
        f"/workspaces/{workspace_id}/members",
        headers=owner_headers,
        json={
            "email": "target@example.com",
            "role": "admin",
        },
    )

    assert response.status_code == 201
    assert response.json()["role"] == "admin"

    # Owner can change an admin's role.
    response = client.put(
        f"/workspaces/{workspace_id}/members/{target_id}",
        headers=owner_headers,
        json={"role": "viewer"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "viewer"

    # Owner can remove that member.
    response = client.delete(
        f"/workspaces/{workspace_id}/members/{target_id}",
        headers=owner_headers,
    )

    assert response.status_code == 200


def test_admin_can_manage_non_admin_members(client, rbac_data):
    workspace_id = rbac_data["workspace"].id
    admin_headers = auth_headers(rbac_data["admin"].id)
    target_id = rbac_data["target"].id

    # Admin can add an editor.
    response = client.post(
        f"/workspaces/{workspace_id}/members",
        headers=admin_headers,
        json={
            "email": "target@example.com",
            "role": "editor",
        },
    )

    assert response.status_code == 201

    # Admin can update a non-admin member.
    response = client.put(
        f"/workspaces/{workspace_id}/members/{target_id}",
        headers=admin_headers,
        json={"role": "viewer"},
    )

    assert response.status_code == 200

    # Admin can remove a non-admin member.
    response = client.delete(
        f"/workspaces/{workspace_id}/members/{target_id}",
        headers=admin_headers,
    )

    assert response.status_code == 200


def test_admin_cannot_assign_or_manage_admin_roles(client, rbac_data):
    workspace_id = rbac_data["workspace"].id
    admin_headers = auth_headers(rbac_data["admin"].id)
    target_id = rbac_data["admin_target"].id

    # Admin cannot assign another admin role.
    response = client.post(
        f"/workspaces/{workspace_id}/members",
        headers=admin_headers,
        json={
            "email": "target@example.com",
            "role": "admin",
        },
    )

    assert response.status_code == 403

    # Admin cannot change an existing admin's role.
    response = client.put(
        f"/workspaces/{workspace_id}/members/{target_id}",
        headers=admin_headers,
        json={"role": "viewer"},
    )

    assert response.status_code == 403

    # Admin cannot remove another admin.
    response = client.delete(
        f"/workspaces/{workspace_id}/members/{target_id}",
        headers=admin_headers,
    )

    assert response.status_code == 403


@pytest.mark.parametrize("role", ["editor", "viewer"])
def test_editor_and_viewer_cannot_manage_members(
    client, rbac_data, role
):
    workspace_id = rbac_data["workspace"].id
    user_id = rbac_data[role].id
    headers = auth_headers(user_id)
    target_id = rbac_data["target"].id

    # Cannot add members.
    response = client.post(
        f"/workspaces/{workspace_id}/members",
        headers=headers,
        json={
            "email": "target@example.com",
            "role": "viewer",
        },
    )

    assert response.status_code == 404

    # Cannot update member roles.
    response = client.put(
        f"/workspaces/{workspace_id}/members/{target_id}",
        headers=headers,
        json={"role": "viewer"},
    )

    assert response.status_code == 404

    # Cannot remove members.
    response = client.delete(
        f"/workspaces/{workspace_id}/members/{target_id}",
        headers=headers,
    )

    assert response.status_code == 404


@pytest.mark.parametrize("role", ["owner", "admin", "editor", "viewer"])
def test_all_workspace_roles_can_list_members(
    client, rbac_data, role
):
    workspace_id = rbac_data["workspace"].id
    user_id = rbac_data[role].id
    headers = auth_headers(user_id)

    response = client.get(
        f"/workspaces/{workspace_id}/members",
        headers=headers,
    )

    assert response.status_code == 200

    members = response.json()
    assert len(members) == 5

    roles = {member["role"] for member in members}

    assert "owner" in roles
    assert "admin" in roles
    assert "editor" in roles
    assert "viewer" in roles


def test_owner_cannot_add_inactive_user(client, rbac_data, test_db):
    inactive_user = User(
        full_name="Inactive User",
        email="inactive@example.com",
        hashed_password="test-hash",
        is_active=False,
    )

    test_db.add(inactive_user)
    test_db.commit()

    workspace_id = rbac_data["workspace"].id
    owner_headers = auth_headers(rbac_data["owner"].id)

    response = client.post(
        f"/workspaces/{workspace_id}/members",
        headers=owner_headers,
        json={
            "email": "inactive@example.com",
            "role": "viewer",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Inactive users cannot be added to a workspace."
    )


def test_owner_cannot_add_themselves_as_member(client, rbac_data):
    workspace_id = rbac_data["workspace"].id
    owner_headers = auth_headers(rbac_data["owner"].id)

    response = client.post(
        f"/workspaces/{workspace_id}/members",
        headers=owner_headers,
        json={
            "email": rbac_data["owner"].email,
            "role": "viewer",
        },
    )

    assert response.status_code == 400


def test_owner_cannot_add_existing_member_again(client, rbac_data):
    workspace_id = rbac_data["workspace"].id
    owner_headers = auth_headers(rbac_data["owner"].id)

    response = client.post(
        f"/workspaces/{workspace_id}/members",
        headers=owner_headers,
        json={
            "email": rbac_data["admin"].email,
            "role": "viewer",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "User is already a workspace member."
    )
