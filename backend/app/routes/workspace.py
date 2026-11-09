
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..database import get_db
from ..models.workspace import Workspace
from ..models.membership import WorkspaceMembership
from ..models.user import User

from ..schemas.workspace import (
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceResponse
)

from ..dependencies import (
    get_current_user,
    get_accessible_workspace,
    get_owned_workspace
)


router = APIRouter(
    prefix="/workspaces",
    tags=["Workspaces"]
)


# CREATE WORKSPACE
@router.post(
    "/",
    response_model=WorkspaceResponse,
    status_code=201
)
def create_workspace(
    workspace_data: WorkspaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    workspace = Workspace(
        name=workspace_data.name,
        description=workspace_data.description,
        owner_id=current_user.id
    )

    db.add(workspace)
    db.commit()
    db.refresh(workspace)

    return workspace


# LIST ACCESSIBLE WORKSPACES
@router.get("/", response_model=list[WorkspaceResponse])
def get_workspaces(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return (
        db.query(Workspace)
        .outerjoin(
            WorkspaceMembership,
            WorkspaceMembership.workspace_id == Workspace.id
        )
        .filter(
            or_(
                Workspace.owner_id == current_user.id,
                WorkspaceMembership.user_id == current_user.id
            )
        )
        .distinct()
        .order_by(Workspace.id.desc())
        .all()
    )


# GET ONE ACCESSIBLE WORKSPACE
@router.get(
    "/{workspace_id}",
    response_model=WorkspaceResponse
)
def get_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_accessible_workspace(
        workspace_id=workspace_id,
        current_user=current_user,
        db=db
    )


# UPDATE WORKSPACE (OWNER ONLY)
@router.put(
    "/{workspace_id}",
    response_model=WorkspaceResponse
)
def update_workspace(
    workspace_id: int,
    workspace_data: WorkspaceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    workspace = get_owned_workspace(
        workspace_id=workspace_id,
        current_user=current_user,
        db=db
    )

    update_data = workspace_data.dict(exclude_unset=True)

    for field, value in update_data.items():
        setattr(workspace, field, value)

    db.commit()
    db.refresh(workspace)

    return workspace


# DELETE WORKSPACE (OWNER ONLY)
@router.delete("/{workspace_id}")
def delete_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    workspace = get_owned_workspace(
        workspace_id=workspace_id,
        current_user=current_user,
        db=db
    )

    db.delete(workspace)
    db.commit()

    return {
        "message": "Workspace deleted successfully"
    }
