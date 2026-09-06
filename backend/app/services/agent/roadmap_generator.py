"""Autonomous Career Coach Agent for resume improvement roadmap generation."""

import logging
from typing import Any

from .gemini import call_gemini
from .prompts.roadmap import ROADMAP_PROMPT
from .tools.coach_tools import (
    tool_fetch_certification_paths,
    tool_search_learning_resources,
)

logger = logging.getLogger(__name__)


def _format_critical_fixes(fixes: list[dict[str, Any]]) -> str:
    valid_fixes = [fix for fix in fixes if isinstance(fix, dict)]
    return "\n".join(
        f"Priority {fix.get('priority', '?')}: {fix.get('issue', '')} - Fix: {fix.get('fix', '')}"
        for fix in sorted(valid_fixes, key=lambda item: item.get("priority", 99))
    ) or "No critical fixes supplied."


def _format_dimensions(dimensions: list[dict[str, Any]]) -> str:
    return "\n".join(
        f"- {dimension.get('name', 'Unknown')}: {dimension.get('score', 'N/A')}/100"
        for dimension in dimensions
        if isinstance(dimension, dict)
    ) or "No dimension scores supplied."


def _format_company_context(company_result: dict[str, Any] | None) -> str:
    if not company_result:
        return "No company-specific context available."
    gaps = "\n".join(
        f"- [{str(gap.get('severity', 'minor')).upper()}] {gap.get('gap', '')}"
        for gap in company_result.get("gap_analysis", [])
        if isinstance(gap, dict)
    ) or "- No company-specific gaps supplied."
    return (
        f"Company: {company_result.get('company_name', 'Unknown')}\n"
        f"Verdict: {company_result.get('verdict', 'N/A')}\n"
        f"Reason: {company_result.get('verdict_reason', '')}\n"
        f"Gaps:\n{gaps}"
    )


def _level_for_score(score: Any) -> str:
    if not isinstance(score, int):
        return "Unassessed"
    if score >= 80:
        return "Strong candidate"
    if score >= 60:
        return "Developing candidate"
    return "Needs focused improvement"


def _add_frontend_aliases(result: dict[str, Any], score: Any) -> None:
    """Keep the existing RoadmapPage working while retaining the richer agent schema."""
    result["current_level"] = _level_for_score(score)
    result["target_level"] = "Application-ready candidate"
    result["roadmap"] = [
        {
            "timeframe": item.get("timeline", ""),
            "task": item.get("action", ""),
            "description": f"{item.get('why', '')} Done when: {item.get('done_when', '')}".strip(),
        }
        for item in result.get("items", [])
        if isinstance(item, dict)
    ]


async def roadmap(
    analysis: dict[str, Any],
    company_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Autonomous Career Coach Agent: searches learning tools & builds grounded, ordered, time-bound improvement roadmap."""
    if not isinstance(analysis, dict) or "error" in analysis:
        return {"error": "ROADMAP_FAILED", "reason": "A valid resume analysis is required"}

    # Extract target role & missing skills for Career Coach Agent tool execution
    target_role = "Software Engineer"
    if company_result and company_result.get("company_name"):
        target_role = company_result.get("company_name")
    elif analysis.get("target_role"):
        target_role = analysis.get("target_role")

    missing_keywords = []
    keyword_match = analysis.get("keyword_match")
    if isinstance(keyword_match, dict):
        missing_keywords = keyword_match.get("missing_keywords", [])

    # Coach Agent Tool Execution 1: Search Learning Resources for top missing skills
    learning_resources = []
    skills_to_search = missing_keywords[:3] if missing_keywords else ["System Design", "Cloud Infrastructure"]
    for skill in skills_to_search:
        res = tool_search_learning_resources(skill)
        learning_resources.append(res)

    # Coach Agent Tool Execution 2: Fetch Industry Certification Paths
    cert_paths = tool_fetch_certification_paths(target_role)

    # Format Coach Tools Context
    coach_tools_context = (
        f"Target Role Certification Paths: {cert_paths}\n"
        f"Recommended Learning Resources: {learning_resources}"
    )

    result = await call_gemini(
        ROADMAP_PROMPT.format(
            overall_score=analysis.get("overall_score", "N/A"),
            mode=analysis.get("mode", "general"),
            is_fresher=analysis.get("is_fresher", False),
            critical_fixes_formatted=_format_critical_fixes(analysis.get("critical_fixes", [])),
            dimension_scores_formatted=_format_dimensions(analysis.get("dimensions", [])),
            company_context=_format_company_context(company_result),
            coach_tools_context=coach_tools_context,
        ),
        expect_json=True,
    )

    if not isinstance(result, dict) or "error" in result:
        return result

    if not result.get("items"):
        logger.warning("Roadmap returned no items; inserting a focused fallback")
        result["items"] = [
            {
                "order": 1,
                "action": "Resolve the highest-priority resume fix and run a fresh analysis.",
                "why": "The generated roadmap contained no specific actions.",
                "timeline": "1 week",
                "done_when": "The top fix is complete and a new analysis result is available.",
            }
        ]

    # Attach Career Coach Agent tool outputs
    result["learning_resources"] = learning_resources
    result["certification_paths"] = cert_paths

    _add_frontend_aliases(result, analysis.get("overall_score"))
    return result
