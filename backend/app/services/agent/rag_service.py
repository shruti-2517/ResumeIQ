"""RAG Service utilizing Gemini embeddings and native PostgreSQL pgvector similarity search."""

import logging
import os
import re
from typing import Any

from google import genai
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.jd_embedding import JobDescriptionEmbedding

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = os.environ.get("GEMINI_EMBEDDING_MODEL", "text-embedding-004")
_genai_client: Any = None


def _get_genai_client() -> Any:
    global _genai_client
    if _genai_client is None:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY is not configured for embeddings")
        _genai_client = genai.Client(api_key=api_key)
    return _genai_client


async def generate_embedding(text: str) -> list[float]:
    """Generate a vector embedding using Google Gemini text-embedding-004."""
    try:
        client = _get_genai_client()
        cleaned_text = text.strip()[:2000]
        if not cleaned_text:
            return [0.0] * 768

        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=cleaned_text,
        )
        if hasattr(response, "embedding") and hasattr(response.embedding, "values"):
            return list(response.embedding.values)
        elif hasattr(response, "embeddings") and len(response.embeddings) > 0:
            return list(response.embeddings[0].values)
        else:
            raise ValueError("Unexpected response format from embedding API")
    except Exception as exc:
        logger.error("Failed to generate embedding via Gemini: %s", exc, exc_info=True)
        return [0.0] * 768


def chunk_text(text: str, chunk_size: int = 600, overlap: int = 100) -> list[str]:
    """Split input text into overlapping semantic chunks."""
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= chunk_size:
        return [cleaned] if cleaned else []

    chunks = []
    start = 0
    while start < len(cleaned):
        end = start + chunk_size
        chunk = cleaned[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


async def seed_job_description(
    role_title: str,
    company: str | None,
    jd_text: str,
    db: AsyncSession,
) -> int:
    """Chunk, embed, and store job description vectors in PostgreSQL via pgvector."""
    chunks = chunk_text(jd_text)
    saved_count = 0

    for chunk in chunks:
        vector = await generate_embedding(chunk)
        jd_embedding = JobDescriptionEmbedding(
            role_title=role_title,
            company=company,
            content_chunk=chunk,
            embedding=vector,
        )
        db.add(jd_embedding)
        saved_count += 1

    await db.commit()
    logger.info("Successfully seeded %d vector chunks for role '%s'", saved_count, role_title)
    return saved_count


async def search_similar_jds(
    query_text: str,
    db: AsyncSession,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Perform vector similarity search using native pgvector cosine distance."""
    query_vector = await generate_embedding(query_text)

    stmt = (
        select(JobDescriptionEmbedding)
        .order_by(JobDescriptionEmbedding.embedding.cosine_distance(query_vector))
        .limit(limit)
    )

    result = await db.execute(stmt)
    rows = result.scalars().all()

    return [
        {
            "id": str(row.id),
            "role_title": row.role_title,
            "company": row.company,
            "content_chunk": row.content_chunk,
        }
        for row in rows
    ]


async def build_rag_context(
    target_role: str | None,
    target_company: str | None,
    resume_text: str,
    db: AsyncSession,
) -> str:
    """Retrieve top relevant vector chunks and format them into an LLM prompt context."""
    query_terms = [t for t in [target_role, target_company] if t]
    query_str = " ".join(query_terms) if query_terms else resume_text[:500]

    similar_chunks = await search_similar_jds(query_str, db, limit=3)
    if not similar_chunks:
        return "No external vector benchmark context available."

    context_lines = ["--- INDUSTRY BENCHMARKS & JOB DESCRIPTION RAG CONTEXT ---"]
    for idx, match in enumerate(similar_chunks, 1):
        context_lines.append(
            f"[Ref {idx}] Role: {match['role_title']} | Company: {match.get('company') or 'Standard'}\n"
            f"Requirements/Key Attributes: {match['content_chunk']}\n"
        )
    context_lines.append("---------------------------------------------------------")
    return "\n".join(context_lines)
