"""Job description vector embedding model for RAG search."""

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class JobDescriptionEmbedding(Base):
    __tablename__ = "jd_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_title: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_chunk: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(768), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
