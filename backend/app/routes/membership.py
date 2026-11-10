
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..database import get_db
from ..models.user import User
from ..models.membership import WorkspaceMembership
from ..dependencies import (
    get_current_user,
    get_accessible_workspace,
    get_manageable_workspace,
)
from ..schemas.membership import (
    MembershipCreate,
    MembershipUpdate,
)

router = APIRouter(
    prefix="/workspaces",
    tags=["Workspace Memberships"],
)


def check_member_management_permission(
    workspace,
    current_user,
    target_role=None,
):
    """Apply Owner/Admin restrictions to membership operations."""

    if workspace.owner_id == current_user.id:
        return

    # Admin cannot assign another Admin role.
    if target_role == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the workspace owner can assign admin roles.",
        )


# LIST MEMBERS
@router.get("/{workspace_id}/members")
def list_members(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workspace = get_accessible_workspace(
        workspace_id, current_user, db
    )

    memberships = (
        db.query(WorkspaceMembership, User)
        .join(User, User.id == WorkspaceMembership.user_id)
        .filter(WorkspaceMembership.workspace_id == workspace_id)
        .all()
    )

    members = []

    for membership, user in memberships:
        members.append({
            "id": membership.id,
            "workspace_id": membership.workspace_id,
            "user_id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "role": membership.role,
            "joined_at": membership.joined_at,
        })

    # Include workspace owner separately.
    owner = db.query(User).filter(
        User.id == workspace.owner_id
    ).first()

    if owner:
        members.insert(0, {
            "id": 0,
            "workspace_id": workspace_id,
            "user_id": owner.id,
            "full_name": owner.full_name,
            "email": owner.email,
            "role": "owner",
            "joined_at": workspace.created_at,
        })

    return members


# ADD MEMBER
@router.post(
    "/{workspace_id}/members",
    status_code=status.HTTP_201_CREATED,
)
def add_member(
    workspace_id: int,
    member_data: MembershipCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workspace = get_manageable_workspace(
        workspace_id, current_user, db
    )

    check_member_management_permission(
        workspace, current_user, member_data.role
    )

    target_user = db.query(User).filter(
        User.email == member_data.email.lower()
    ).first()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account not found.",
        )

    # Prevent inactive accounts from joining workspaces.
    if not target_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive users cannot be added to a workspace.",
        )

    if target_user.id == workspace.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace owner cannot be added as a member.",
        )

    existing = db.query(WorkspaceMembership).filter(
        WorkspaceMembership.workspace_id == workspace_id,
        WorkspaceMembership.user_id == target_user.id,
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a workspace member.",
        )

    membership = WorkspaceMembership(
        workspace_id=workspace_id,
        user_id=target_user.id,
        role=member_data.role,
    )

    db.add(membership)

    try:
        db.commit()
        db.refresh(membership)

    except IntegrityError:
        db.rollback()

        # Handle a duplicate created by a concurrent request.
        existing = db.query(WorkspaceMembership).filter(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.user_id == target_user.id,
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already a workspace member.",
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Membership could not be created because of a database conflict.",
        )

    return {
        "message": "Member added successfully.",
        "membership_id": membership.id,
        "user_id": target_user.id,
        "role": membership.role,
    }


# UPDATE MEMBER ROLE
@router.put("/{workspace_id}/members/{user_id}")
def update_member_role(
    workspace_id: int,
    user_id: int,
    member_data: MembershipUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workspace = get_manageable_workspace(
        workspace_id, current_user, db
    )

    check_member_management_permission(
        workspace, current_user, member_data.role
    )

    if user_id == workspace.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace owner role cannot be changed.",
        )

    membership = db.query(WorkspaceMembership).filter(
        WorkspaceMembership.workspace_id == workspace_id,
        WorkspaceMembership.user_id == user_id,
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace member not found.",
        )

    # Only the owner can modify an existing Admin.
    if (
        membership.role == "admin"
        and workspace.owner_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner can change an admin role.",
        )

    membership.role = member_data.role

    db.commit()

    return {
        "message": "Member role updated successfully.",
        "user_id": user_id,
        "role": membership.role,
    }


# REMOVE MEMBER
@router.delete("/{workspace_id}/members/{user_id}")
def remove_member(
    workspace_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workspace = get_manageable_workspace(
        workspace_id, current_user, db
    )

    if user_id == workspace.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace owner cannot be removed.",
        )

    membership = db.query(WorkspaceMembership).filter(
        WorkspaceMembership.workspace_id == workspace_id,
        WorkspaceMembership.user_id == user_id,
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace member not found.",
        )

    # Only the owner can remove an Admin.
    if (
        membership.role == "admin"
        and workspace.owner_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner can remove an admin.",
        )

    db.delete(membership)
    db.commit()

    return {
        "message": "Member removed successfully.",
        "user_id": user_id,
    }
