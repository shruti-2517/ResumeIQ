"""Tool declarations and execution handlers for the Resume Auditor Agent."""

import logging
import re
from typing import Any

from google.genai import types
from app.services.parser.ats_checker import check_ats_readability
from app.services.agent.rag_service import search_similar_jds

logger = logging.getLogger(__name__)


def tool_check_ats_readability(raw_text: str, file_type: str = "pdf") -> dict[str, Any]:
    """Inspect resume text and layout for ATS readability and hazard compatibility."""
    try:
        file_bytes = raw_text.encode("utf-8")
        return check_ats_readability(file_bytes, file_type)
    except Exception as exc:
        logger.error("tool_check_ats_readability failed: %s", exc)
        return {"ats_score": 75, "readability_level": "Medium", "warnings": [], "found_sections": [], "layout_hazards": []}


async def tool_retrieve_vector_benchmarks(query_text: str, db: Any = None) -> dict[str, Any]:
    """Retrieve matching industry benchmark vector chunks from PostgreSQL pgvector store."""
    if db is None:
        return {"chunks": [], "message": "No database session available for RAG search"}
    try:
        chunks = await search_similar_jds(query_text, db, limit=3)
        return {"chunks": chunks, "count": len(chunks)}
    except Exception as exc:
        logger.error("tool_retrieve_vector_benchmarks failed: %s", exc)
        return {"chunks": [], "error": str(exc)}


def tool_extract_keyword_gaps(resume_text: str, job_description: str) -> dict[str, Any]:
    """Extract matched, missing, and partial keyword gaps between resume and target job description."""
    if not job_description or job_description.strip() == "Not provided":
        return {
            "match_percentage": 100,
            "matched_keywords": [],
            "missing_keywords": [],
            "partial_keywords": [],
        }

    resume_words = set(re.findall(r"\b[A-Za-z0-9+#\.\-]{2,}\b", resume_text.lower()))
    jd_words = re.findall(r"\b[A-Za-z0-9+#\.\-]{2,}\b", job_description.lower())

    # Extract distinct technical terms (words appearing in JD that look like tech skills)
    common_stopwords = {"and", "the", "with", "for", "that", "this", "from", "you", "will", "our", "are", "have", "must", "work"}
    jd_terms = list(dict.fromkeys([w for w in jd_words if len(w) > 2 and w not in common_stopwords]))[:25]

    matched = []
    missing = []

    for term in jd_terms:
        if term in resume_words:
            matched.append(term.capitalize())
        else:
            missing.append(term.capitalize())

    total = len(jd_terms)
    match_pct = round((len(matched) / total * 100)) if total > 0 else 85

    return {
        "match_percentage": min(100, max(0, match_pct)),
        "matched_keywords": matched[:10],
        "missing_keywords": missing[:10],
        "partial_keywords": [],
    }


# Gemini Function Declarations
check_ats_decl = types.FunctionDeclaration(
    name="tool_check_ats_readability",
    description="Inspect resume layout structure for ATS parsing compatibility, multi-column bleeding, and tables.",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "raw_text": types.Schema(type="STRING", description="The full resume text"),
            "file_type": types.Schema(type="STRING", description="File extension, e.g. pdf or docx"),
        },
        required=["raw_text"],
    ),
)

retrieve_rag_decl = types.FunctionDeclaration(
    name="tool_retrieve_vector_benchmarks",
    description="Retrieve industry benchmark vector chunks and target job description data from pgvector database.",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "query_text": types.Schema(type="STRING", description="The search query or target role"),
        },
        required=["query_text"],
    ),
)

extract_keywords_decl = types.FunctionDeclaration(
    name="tool_extract_keyword_gaps",
    description="Compute keyword match percentage, matched skills, missing critical keywords, and partial matches between resume and job description.",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "resume_text": types.Schema(type="STRING", description="Candidate resume text"),
            "job_description": types.Schema(type="STRING", description="Target job description text"),
        },
        required=["resume_text", "job_description"],
    ),
)

AUDITOR_TOOLS = types.Tool(
    function_declarations=[check_ats_decl, retrieve_rag_decl, extract_keywords_decl]
)


async def execute_auditor_tool(tool_name: str, tool_args: dict[str, Any], db: Any = None) -> dict[str, Any]:
    """Execute auditor tool function by name."""
    logger.info("Auditor Agent executing tool '%s' with args: %s", tool_name, list(tool_args.keys()))
    if tool_name == "tool_check_ats_readability":
        return tool_check_ats_readability(
            raw_text=tool_args.get("raw_text", ""),
            file_type=tool_args.get("file_type", "pdf"),
        )
    elif tool_name == "tool_retrieve_vector_benchmarks":
        return await tool_retrieve_vector_benchmarks(
            query_text=tool_args.get("query_text", ""),
            db=db,
        )
    elif tool_name == "tool_extract_keyword_gaps":
        return tool_extract_keyword_gaps(
            resume_text=tool_args.get("resume_text", ""),
            job_description=tool_args.get("job_description", ""),
        )
    else:
        return {"error": "UNKNOWN_TOOL", "message": f"Unknown tool name: {tool_name}"}
