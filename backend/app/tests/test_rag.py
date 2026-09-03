"""Unit tests for Stage 1 RAG service and vector utilities."""

import pytest
from app.services.agent.rag_service import chunk_text


def test_chunk_text_basic():
    text = "This is a short sentence."
    chunks = chunk_text(text, chunk_size=100)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_text_splitting():
    long_text = "Word " * 200  # 1000 chars approx
    chunks = chunk_text(long_text, chunk_size=300, overlap=50)
    assert len(chunks) > 1
    assert all(len(c) <= 300 for c in chunks)


def test_rag_imports():
    from app.models import JobDescriptionEmbedding
    from app.services.agent.rag_service import build_rag_context, generate_embedding, search_similar_jds

    assert JobDescriptionEmbedding.__tablename__ == "jd_embeddings"
    assert callable(build_rag_context)
    assert callable(generate_embedding)
    assert callable(search_similar_jds)
