"""Resume analysis pipeline with RAG context and fresher-mode switching."""

import logging
from typing import Any

from .gemini import call_gemini
from .prompts.analysis import FRESHER_ANALYSIS_PROMPT, GENERAL_ANALYSIS_PROMPT
from .rag_service import build_rag_context, seed_job_description

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
    """Analyze a resume using Gemini, augmented with RAG context and JD keyword matching."""
    if not isinstance(raw_text, str) or not raw_text.strip():
        return {"error": "ANALYSIS_FAILED", "reason": "Resume text is empty"}

    target = target_role.strip() if isinstance(target_role, str) and target_role.strip() else "Not specified"
    jd = job_description.strip() if isinstance(job_description, str) and job_description.strip() else "Not provided"

    # Seed JD into RAG embeddings if provided and DB session is available
    if db is not None and jd != "Not provided":
        try:
            await seed_job_description(
                role_title=target if target != "Not specified" else "Target Role",
                company=None,
                jd_text=jd,
                db=db,
            )
        except Exception as exc:
            logger.warning("Failed to seed JD into RAG embeddings: %s", exc)

    # Retrieve RAG context if DB session is available
    rag_context = ""
    if db is not None:
        try:
            rag_context = await build_rag_context(target_role, None, raw_text, db)
        except Exception as exc:
            logger.warning("Failed to build RAG context: %s", exc)

    prompt_str = GENERAL_ANALYSIS_PROMPT.format(
        resume_text=raw_text,
        target_role=target,
        job_description=jd,
        rag_context=rag_context,
    )

    result = await call_gemini(prompt_str, expect_json=True)
    if not isinstance(result, dict) or "error" in result:
        return result

    if result.get("is_fresher") is True:
        logger.info("Fresher resume detected; rerunning analysis in fresher mode")
        fresher_prompt_str = FRESHER_ANALYSIS_PROMPT.format(
            resume_text=raw_text,
            target_role=target,
            job_description=jd,
            rag_context=rag_context,
        )
        result = await call_gemini(fresher_prompt_str, expect_json=True)
        if not isinstance(result, dict) or "error" in result:
            return result
        error = _validate_analysis(result, "fresher")
        return error or result

    error = _validate_analysis(result, "general")
    return error or result
