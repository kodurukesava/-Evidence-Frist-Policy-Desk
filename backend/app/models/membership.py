
from sqlalchemy import (
    Column, Integer, String, DateTime,
    ForeignKey, UniqueConstraint
)
from sqlalchemy.sql import func

from ..database import Base


class WorkspaceMembership(Base):
    __tablename__ = "workspace_memberships"

    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "user_id",
            name="uq_workspace_user"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    workspace_id = Column(
        Integer,
        ForeignKey("workspaces.id"),
        nullable=False
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    role = Column(String(30), default="viewer", nullable=False)

    joined_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
