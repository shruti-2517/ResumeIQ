"""Unit tests for Stage 5 SSE Streaming & E2E Validation."""

import json
import pytest
from app.routers.resume import _analysis_stream_generator


class DummySession:
    id = "11111111-1111-1111-1111-111111111111"
    raw_text = "Software Engineer with Python experience..."
    file_type = "pdf"


@pytest.mark.asyncio
async def test_analysis_stream_generator_mock(monkeypatch):
    async def mock_run_and_store(db, session, target_role, job_description):
        return {"overall_score": 90, "mode": "general"}

    monkeypatch.setattr("app.routers.resume._run_and_store_analysis", mock_run_and_store)

    events = []
    async for event in _analysis_stream_generator(None, DummySession(), "Backend Dev", "Python JD"):
        events.append(event)

    assert len(events) == 4
    assert events[0]["event"] == "progress"

    step1_data = json.loads(events[0]["data"])
    assert step1_data["step"] == 1
    assert step1_data["progress_percentage"] == 25

    step4_data = json.loads(events[3]["data"])
    assert step4_data["step"] == 4
    assert step4_data["progress_percentage"] == 100
    assert step4_data["result"]["overall_score"] == 90
