"""Autonomous Resume Auditor Agent with tool execution and fresher calibration."""

import logging
from typing import Any

from .gemini import call_gemini
from .prompts.analysis import FRESHER_ANALYSIS_PROMPT, GENERAL_ANALYSIS_PROMPT
from .rag_service import build_rag_context, seed_job_description
from .tools.auditor_tools import (
    tool_check_ats_readability,
    tool_extract_keyword_gaps,
    tool_retrieve_vector_benchmarks,
)

logger = logging.getLogger(__name__)

EXPECTED_DIMENSIONS = {
    "ATS Compatibility",
    "Impact & Quantification",
    "Skill Relevance",
    "Language & Authenticity",
    "Structure & Readability",
    "Completeness",
    "Competitive Standing",
}


def _validate_analysis(result: dict[str, Any], expected_mode: str) -> dict[str, Any] | None:
    score = result.get("overall_score")
    dimensions = result.get("dimensions")
    if not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 100:
        return {"error": "ANALYSIS_FAILED", "reason": "Analysis returned an invalid overall score"}
    if not isinstance(dimensions, list) or len(dimensions) != len(EXPECTED_DIMENSIONS):
        return {"error": "ANALYSIS_FAILED", "reason": "Analysis did not return all 7 dimensions"}

    names: set[str] = set()
    for dimension in dimensions:
        if not isinstance(dimension, dict):
            return {"error": "ANALYSIS_FAILED", "reason": "Analysis returned an invalid dimension"}
        name = dimension.get("name")
        dimension_score = dimension.get("score")
        if not isinstance(name, str) or not name.strip():
            return {"error": "ANALYSIS_FAILED", "reason": "Analysis dimension name was missing"}
        if (
            not isinstance(dimension_score, int)
            or isinstance(dimension_score, bool)
            or not 0 <= dimension_score <= 100
        ):
            return {"error": "ANALYSIS_FAILED", "reason": f"Invalid score for {name}"}
        names.add(name)

    if names != EXPECTED_DIMENSIONS:
        return {"error": "ANALYSIS_FAILED", "reason": "Analysis returned unexpected dimensions"}
    if expected_mode == "fresher":
        result["mode"] = "fresher"
        result["is_fresher"] = True
    elif result.get("mode") != "general":
        result["mode"] = "general"
    return None


async def analyze(
    raw_text: str,
    target_role: str | None = None,
    job_description: str | None = None,
    db: Any = None,
) -> dict[str, Any]:
    """Autonomous Resume Auditor Agent: executes tools and analyzes resume with Gemini."""
    if not isinstance(raw_text, str) or not raw_text.strip():
        return {"error": "ANALYSIS_FAILED", "reason": "Resume text is empty"}

    target = target_role.strip() if isinstance(target_role, str) and target_role.strip() else "Not specified"
    jd = job_description.strip() if isinstance(job_description, str) and job_description.strip() else "Not provided"

    # Agent Tool Execution Step 1: Execute ATS layout readability tool
    ats_tool_data = tool_check_ats_readability(raw_text, "pdf")

    # Agent Tool Execution Step 2: Seed JD and query pgvector store
    if db is not None and jd != "Not provided":
        try:
            await seed_job_description(
                role_title=target if target != "Not specified" else "Target Role",
                company=None,
                jd_text=jd,
                db=db,
            )
        except Exception as exc:
            logger.warning("Agent JD seeding warning: %s", exc)

    # Agent Tool Execution Step 3: Retrieve vector benchmarks
    rag_context = ""
    if db is not None:
        try:
            rag_context = await build_rag_context(target_role, None, raw_text, db)
        except Exception as exc:
            logger.warning("Agent RAG retrieval warning: %s", exc)

    # Agent Tool Execution Step 4: Extract keyword gaps
    keyword_tool_data = tool_extract_keyword_gaps(raw_text, jd)

    # Synthesize Auditor Agent prompt with tool ground truths
    prompt_str = GENERAL_ANALYSIS_PROMPT.format(
        resume_text=raw_text,
        target_role=target,
        job_description=jd,
        rag_context=f"{rag_context}\n\nATS Layout Inspection: {ats_tool_data}\nKeyword Gap Tool: {keyword_tool_data}",
    )

    result = await call_gemini(prompt_str, expect_json=True)
    if not isinstance(result, dict) or "error" in result:
        return result

    # Attach tool outputs to final agent result
    result["ats_health"] = ats_tool_data
    if "keyword_match" not in result or not isinstance(result["keyword_match"], dict):
        result["keyword_match"] = keyword_tool_data

    if result.get("is_fresher") is True:
        logger.info("Fresher resume detected by Auditor Agent; recalibrating in fresher mode")
        fresher_prompt_str = FRESHER_ANALYSIS_PROMPT.format(
            resume_text=raw_text,
            target_role=target,
            job_description=jd,
            rag_context=f"{rag_context}\n\nATS Layout Inspection: {ats_tool_data}\nKeyword Gap Tool: {keyword_tool_data}",
        )
        result = await call_gemini(fresher_prompt_str, expect_json=True)
        if not isinstance(result, dict) or "error" in result:
            return result
        result["ats_health"] = ats_tool_data
        if "keyword_match" not in result or not isinstance(result["keyword_match"], dict):
            result["keyword_match"] = keyword_tool_data
        error = _validate_analysis(result, "fresher")
        return error or result

    error = _validate_analysis(result, "general")
    return error or result
