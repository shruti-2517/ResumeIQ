"""Unit tests for Stage 3 RAG-augmented Analysis & JD Keyword Matcher Backend."""

from app.schemas.analysis import AnalysisRequest
from app.services.agent.prompts.analysis import GENERAL_ANALYSIS_PROMPT, FRESHER_ANALYSIS_PROMPT


def test_analysis_request_schema():
    req = AnalysisRequest(target_role="Senior Python Engineer", job_description="Must know FastAPI and PostgreSQL")
    assert req.target_role == "Senior Python Engineer"
    assert req.job_description == "Must know FastAPI and PostgreSQL"


def test_prompts_formatting():
    formatted = GENERAL_ANALYSIS_PROMPT.format(
        resume_text="Experienced Backend Developer...",
        target_role="Backend Developer",
        job_description="Requires Python, FastAPI, Docker",
        rag_context="[Ref 1] Industry Benchmark for Backend Developer",
    )
    assert "Experienced Backend Developer..." in formatted
    assert "Requires Python, FastAPI, Docker" in formatted
    assert "[Ref 1] Industry Benchmark for Backend Developer" in formatted
    assert "keyword_match" in formatted


def test_fresher_prompt_formatting():
    formatted = FRESHER_ANALYSIS_PROMPT.format(
        resume_text="CS Student with open source projects...",
        target_role="Software Intern",
        job_description="Internship role",
        rag_context="[Ref 1] Student Benchmark",
    )
    assert "CS Student with open source projects..." in formatted
    assert "keyword_match" in formatted
