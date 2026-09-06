"""Unit tests for Stage C Multi-Agent Supervisor Orchestrator Gateway & Tool Call Logs."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from app.routers.resume import get_agent_logs
from app.services.agent_gateway import (
    AGENT_NAME_MAP,
    clear_tool_logs,
    get_supervisor_state,
    get_tool_logs,
    invoke,
    log_tool_execution,
)


@pytest.fixture(autouse=True)
def _reset_logs():
    clear_tool_logs()
    yield
    clear_tool_logs()


def test_supervisor_state_initialization():
    state = get_supervisor_state()
    assert state["supervisor_status"] == "ONLINE"
    assert "metrics" in state
    assert "Resume Auditor Agent" in state["registered_agents"]
    assert "Career Coach Agent" in state["registered_agents"]


def test_log_tool_execution_and_retrieval():
    log_tool_execution(
        agent_name="Resume Auditor Agent",
        tool_name="tool_check_ats_readability",
        tool_args={"raw_text": "Sample Resume"},
        execution_time_ms=12.5,
        status="success",
    )
    log_tool_execution(
        agent_name="Career Coach Agent",
        tool_name="tool_search_learning_resources",
        tool_args={"skill_name": "Docker"},
        execution_time_ms=45.2,
        status="success",
    )

    logs = get_tool_logs()
    assert len(logs) == 2
    assert logs[0]["agent_name"] == "Career Coach Agent"
    assert logs[0]["tool_name"] == "tool_search_learning_resources"
    assert logs[1]["agent_name"] == "Resume Auditor Agent"


@pytest.mark.anyio
async def test_supervisor_gateway_invocation_telemetry():
    mock_agent_fn = AsyncMock(return_value={"overall_score": 85, "mode": "general"})

    with patch("app.services.agent_gateway._agent_function", return_value=mock_agent_fn):
        result = await invoke("analyze", raw_text="Experienced Python Developer")

        assert "overall_score" in result
        assert "_supervisor_telemetry" in result
        assert result["_supervisor_telemetry"]["agent_name"] == "Resume Auditor Agent"
        assert result["_supervisor_telemetry"]["execution_time_ms"] >= 0

        state = get_supervisor_state()
        assert state["metrics"]["total_agent_invocations"] > 0
        assert state["metrics"]["last_active_agent"] == "Resume Auditor Agent"


@pytest.mark.anyio
async def test_agent_logs_endpoint():
    session_id = uuid4()
    mock_session = MagicMock()
    mock_session.id = session_id

    mock_db = AsyncMock()

    with patch("app.routers.resume._get_session", new_callable=AsyncMock) as mock_get_session:
        mock_get_session.return_value = mock_session

        log_tool_execution(
            agent_name="Company Analyst Agent",
            tool_name="analyze_company_fit",
            tool_args={"company_name": "Google"},
            execution_time_ms=30.0,
        )

        response = await get_agent_logs(session_id=session_id, db=mock_db)

        assert response["session_id"] == str(session_id)
        assert response["supervisor_state"]["supervisor_status"] == "ONLINE"
        assert len(response["tool_logs"]) >= 1
        assert response["tool_logs"][0]["agent_name"] == "Company Analyst Agent"
