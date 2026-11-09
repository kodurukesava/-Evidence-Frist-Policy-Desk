
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt

from .database import get_db
from .models.user import User
from .models.workspace import Workspace
from .models.membership import WorkspaceMembership
from .config import JWT_SECRET_KEY, JWT_ALGORITHM


security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )

        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type.",
                headers={"WWW-Authenticate": "Bearer"}
            )

        subject = payload.get("sub")

        if not subject or not str(subject).isdigit():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token.",
                headers={"WWW-Authenticate": "Bearer"}
            )

        user_id = int(subject)

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is inactive."
        )

    return user


def get_accessible_workspace(
    workspace_id: int,
    current_user: User,
    db: Session
):
    workspace = (
        db.query(Workspace)
        .outerjoin(
            WorkspaceMembership,
            WorkspaceMembership.workspace_id == Workspace.id
        )
        .filter(
            Workspace.id == workspace_id,
            (
                (Workspace.owner_id == current_user.id)
                | (WorkspaceMembership.user_id == current_user.id)
            )
        )
        .first()
    )

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found."
        )

    return workspace


def get_owned_workspace(
    workspace_id: int,
    current_user: User,
    db: Session
):
    workspace = (
        db.query(Workspace)
        .filter(
            Workspace.id == workspace_id,
            Workspace.owner_id == current_user.id
        )
        .first()
    )

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found."
        )

    return workspace

def get_editable_workspace(
    workspace_id: int,
    current_user: User,
    db: Session,
):
    workspace = get_accessible_workspace(
        workspace_id=workspace_id,
        current_user=current_user,
        db=db,
    )

    if workspace.owner_id == current_user.id:
        return workspace

    membership = (
        db.query(WorkspaceMembership)
        .filter(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.user_id == current_user.id,
        )
        .first()
    )

    if not membership or membership.role not in {"editor", "admin"}:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found.",
        )

    return workspace
