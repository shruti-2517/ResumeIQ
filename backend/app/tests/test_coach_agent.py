"""Unit tests for Stage B Autonomous Career Coach Agent & Learning Search Tools."""

from unittest.mock import AsyncMock, patch

import pytest
from app.services.agent.roadmap_generator import roadmap
from app.services.agent.tools.coach_tools import (
    COACH_TOOLS,
    execute_coach_tool,
    tool_fetch_certification_paths,
    tool_search_learning_resources,
)


def test_coach_tool_declarations():
    assert len(COACH_TOOLS.function_declarations) == 2
    names = [fn.name for fn in COACH_TOOLS.function_declarations]
    assert "tool_search_learning_resources" in names
    assert "tool_fetch_certification_paths" in names


def test_tool_search_learning_resources():
    res = tool_search_learning_resources("Python")
    assert res["skill"] == "Python"
    assert len(res["courses"]) > 0
    assert "url" in res["courses"][0]
    assert res["total_resources"] > 0


def test_tool_fetch_certification_paths():
    res = tool_fetch_certification_paths("DevOps Engineer")
    assert res["role"] == "DevOps Engineer"
    assert len(res["certifications"]) > 0
    assert len(res["recommended_path"]) > 0
    assert "AWS" in res["certifications"][0]["name"] or "Linux" in res["certifications"][0]["name"]


def test_execute_coach_tool_dispatcher():
    res = execute_coach_tool(
        "tool_search_learning_resources",
        {"skill_name": "Docker"},
    )
    assert res["skill"] == "Docker"
    assert len(res["courses"]) > 0

    unknown = execute_coach_tool("invalid_tool", {})
    assert "error" in unknown


@pytest.mark.anyio
async def test_roadmap_agent_execution():
    mock_analysis = {
        "overall_score": 75,
        "mode": "general",
        "is_fresher": False,
        "critical_fixes": [{"priority": 1, "issue": "Missing cloud skills", "fix": "Learn AWS and Docker"}],
        "dimensions": [
            {"name": "ATS Compatibility", "score": 80},
            {"name": "Impact & Quantification", "score": 70},
            {"name": "Skill Relevance", "score": 75},
            {"name": "Language & Authenticity", "score": 75},
            {"name": "Structure & Readability", "score": 80},
            {"name": "Completeness", "score": 70},
            {"name": "Competitive Standing", "score": 75},
        ],
        "keyword_match": {
            "matched_keywords": ["Python", "FastAPI"],
            "missing_keywords": ["Docker", "Kubernetes", "AWS"],
        },
    }

    mock_gemini_response = {
        "overall_gap_summary": "Candidate lacks containerization and cloud infrastructure experience.",
        "items": [
            {
                "order": 1,
                "action": "Complete Docker and Kubernetes certification training.",
                "why": "Missing keywords in target DevOps role.",
                "timeline": "2 weeks",
                "done_when": "Deployed a multi-container app on k8s.",
            }
        ],
        "resume_ready_estimate": "3 weeks",
    }

    with patch("app.services.agent.roadmap_generator.call_gemini", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_gemini_response
        result = await roadmap(analysis=mock_analysis)

        assert "error" not in result
        assert result["overall_gap_summary"] == mock_gemini_response["overall_gap_summary"]
        assert len(result["items"]) == 1
        assert len(result["learning_resources"]) > 0
        assert "certification_paths" in result
        # Check backward compatibility fields for frontend UI
        assert "current_level" in result
        assert "target_level" in result
        assert "roadmap" in result
        assert result["roadmap"][0]["task"] == "Complete Docker and Kubernetes certification training."
