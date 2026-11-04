
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.workspace import Workspace
from ..schemas.workspace import (
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceResponse
)

router = APIRouter(
    prefix="/workspaces",
    tags=["Workspaces"]
)


@router.post(
    "/",
    response_model=WorkspaceResponse,
    status_code=201
)
def create_workspace(
    workspace_data: WorkspaceCreate,
    db: Session = Depends(get_db)
):
    # Temporary owner ID for development.
    owner_id = 1

    workspace = Workspace(
        name=workspace_data.name,
        description=workspace_data.description,
        owner_id=owner_id
    )

    db.add(workspace)
    db.commit()
    db.refresh(workspace)

    return workspace


@router.get("/", response_model=list[WorkspaceResponse])
def get_workspaces(db: Session = Depends(get_db)):
    return db.query(Workspace).order_by(
        Workspace.id.desc()
    ).all()


@router.get(
    "/{workspace_id}",
    response_model=WorkspaceResponse
)
def get_workspace(
    workspace_id: int,
    db: Session = Depends(get_db)
):
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id
    ).first()

    if not workspace:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found"
        )

    return workspace


@router.put(
    "/{workspace_id}",
    response_model=WorkspaceResponse
)
def update_workspace(
    workspace_id: int,
    workspace_data: WorkspaceUpdate,
    db: Session = Depends(get_db)
):
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id
    ).first()

    if not workspace:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found"
        )

    update_data = workspace_data.dict(exclude_unset=True)

    for field, value in update_data.items():
        setattr(workspace, field, value)

    db.commit()
    db.refresh(workspace)

    return workspace


@router.delete("/{workspace_id}")
def delete_workspace(
    workspace_id: int,
    db: Session = Depends(get_db)
):
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id
    ).first()

    if not workspace:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found"
        )

    db.delete(workspace)
    db.commit()

    return {"message": "Workspace deleted successfully"}
