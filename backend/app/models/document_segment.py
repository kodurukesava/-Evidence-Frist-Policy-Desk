
from sqlalchemy import (
    Column, Integer, String, Text,
    DateTime, ForeignKey
)
from sqlalchemy.sql import func

from ..database import Base


class DocumentSegment(Base):
    __tablename__ = "document_segments"

    id = Column(Integer, primary_key=True, index=True)

    document_version_id = Column(
        Integer,
        ForeignKey("document_versions.id"),
        nullable=False
    )

    segment_index = Column(Integer, nullable=False)

    segment_type = Column(
        String(30),
        default="text",
        nullable=False
    )

    section_title = Column(String(255), nullable=True)

    content = Column(Text, nullable=False)

    page_number = Column(Integer, nullable=True)

    slide_number = Column(Integer, nullable=True)

    sheet_name = Column(String(255), nullable=True)

    row_start = Column(Integer, nullable=True)

    row_end = Column(Integer, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
