"""Create vector extension and jd_embeddings table.

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-03
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 2. Create jd_embeddings table
    op.create_table(
        "jd_embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("role_title", sa.String(length=255), nullable=False),
        sa.Column("company", sa.String(length=255), nullable=True),
        sa.Column("content_chunk", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(768), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # 3. Create HNSW index for cosine distance vector similarity search
    op.execute(
        "CREATE INDEX idx_jd_embeddings_vector ON jd_embeddings USING hnsw (embedding vector_cosine_ops);"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_jd_embeddings_vector;")
    op.drop_table("jd_embeddings")
