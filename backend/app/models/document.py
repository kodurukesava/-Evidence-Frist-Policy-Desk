
from sqlalchemy import (
    Column,
    Integer,
    String,
    BigInteger,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.sql import func

from ..database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    workspace_id = Column(
        Integer,
        ForeignKey("workspaces.id"),
        nullable=False,
    )

    uploaded_by_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    original_filename = Column(
        String(255),
        nullable=False,
    )

    stored_filename = Column(
        String(255),
        nullable=False,
    )

    file_type = Column(
        String(20),
        nullable=False,
    )

    file_size = Column(
        BigInteger,
        nullable=False,
    )

    # Document processing status
    status = Column(
        String(30),
        default="uploaded",
        nullable=False,
    )

    # Document lifecycle status
    lifecycle_status = Column(
        String(20),
        default="active",
        nullable=False,
        index=True,
    )

    archived_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Store extracted document text
    extracted_text = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
