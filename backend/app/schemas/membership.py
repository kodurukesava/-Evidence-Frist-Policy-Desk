
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr


WorkspaceRole = Literal["admin", "editor", "viewer"]


class MembershipCreate(BaseModel):
    email: EmailStr
    role: WorkspaceRole = "viewer"


class MembershipUpdate(BaseModel):
    role: WorkspaceRole


class MembershipResponse(BaseModel):
    id: int
    workspace_id: int
    user_id: int
    full_name: str
    email: EmailStr
    role: WorkspaceRole
    joined_at: datetime

    class Config:
        from_attributes = True
