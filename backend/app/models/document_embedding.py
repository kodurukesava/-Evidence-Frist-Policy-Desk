
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    JSON,
)
from sqlalchemy.sql import func

from ..database import Base


class DocumentEmbedding(Base):
    __tablename__ = "document_embeddings"

    __table_args__ = (
        UniqueConstraint(
            "segment_id",
            "model_name",
            name="uq_segment_embedding_model",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    segment_id = Column(
        Integer,
        ForeignKey("document_segments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    model_name = Column(
        String(255),
        nullable=False,
    )

    dimensions = Column(
        Integer,
        nullable=False,
    )

    embedding = Column(
        JSON,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
