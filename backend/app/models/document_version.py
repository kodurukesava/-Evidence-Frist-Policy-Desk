
from sqlalchemy import (
    Column, Integer, String, DateTime,
    Boolean, ForeignKey, UniqueConstraint
)
from sqlalchemy.sql import func

from ..database import Base


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "version_number",
            name="uq_document_version"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    document_id = Column(
        Integer,
        ForeignKey("documents.id"),
        nullable=False
    )

    version_number = Column(Integer, nullable=False)

    checksum = Column(String(64), nullable=True)

    storage_path = Column(String(500), nullable=False)

    effective_from = Column(DateTime(timezone=True), nullable=True)

    effective_to = Column(DateTime(timezone=True), nullable=True)

    is_current = Column(Boolean, default=True, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
