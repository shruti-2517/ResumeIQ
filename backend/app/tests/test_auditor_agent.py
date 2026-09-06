"""Unit tests for Stage A Autonomous Resume Auditor Agent & Tool Declarations."""

import pytest
from app.services.agent.tools.auditor_tools import (
    AUDITOR_TOOLS,
    execute_auditor_tool,
    tool_check_ats_readability,
    tool_extract_keyword_gaps,
)


def test_auditor_tool_declarations():
    assert len(AUDITOR_TOOLS.function_declarations) == 3
    names = [fn.name for fn in AUDITOR_TOOLS.function_declarations]
    assert "tool_check_ats_readability" in names
    assert "tool_retrieve_vector_benchmarks" in names
    assert "tool_extract_keyword_gaps" in names


def test_tool_check_ats_readability_execution():
    res = tool_check_ats_readability("Experience:\nSoftware Engineer at Tech Corp", "pdf")
    assert "ats_score" in res
    assert "readability_level" in res


def test_tool_extract_keyword_gaps_execution():
    res = tool_extract_keyword_gaps(
        resume_text="Experienced with Python, FastAPI, and PostgreSQL",
        job_description="Looking for a developer with Python, Docker, and Kubernetes",
    )
    assert "match_percentage" in res
    assert "matched_keywords" in res
    assert "Python" in res["matched_keywords"]
    assert "Docker" in res["missing_keywords"]


@pytest.mark.asyncio
async def test_execute_auditor_tool_dispatcher():
    res = await execute_auditor_tool("tool_extract_keyword_gaps", {
        "resume_text": "Python FastAPI Developer",
        "job_description": "Python, Docker Developer"
    })
    assert res["match_percentage"] > 0
