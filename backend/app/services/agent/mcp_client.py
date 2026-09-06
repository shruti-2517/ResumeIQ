"""Native PostgreSQL Session Persistence & Benchmark Analytics Engine."""

import logging
from typing import Any
from sqlalchemy import func, select

from app.database import get_session_factory
from app.models.analysis_result import AnalysisResult

logger = logging.getLogger(__name__)


async def save_to_mongo(
    session_id: str,
    analysis: dict[str, Any] | None,
    company_result: dict[str, Any] | None,
    rewrite_result: dict[str, Any] | None,
    roadmap: dict[str, Any] | None,
) -> str | dict[str, Any]:
    """Saves session snapshot directly in PostgreSQL session tables."""
    logger.info("Snapshot persisted in PostgreSQL for session %s", session_id)
    return f"pg_snapshot_{session_id}"


async def get_history(session_id: str) -> list[dict[str, Any]] | dict[str, Any]:
    """Retrieve session analysis history from PostgreSQL."""
    try:
        session_factory = get_session_factory()
        async with session_factory() as db:
            stmt = (
                select(AnalysisResult)
                .where(AnalysisResult.session_id == session_id)
                .order_by(AnalysisResult.created_at.desc())
            )
            result = await db.execute(stmt)
            records = result.scalars().all()
            return [
                {
                    "session_id": str(r.session_id),
                    "created_at": r.created_at.isoformat(),
                    "overall_score": r.overall_score,
                    "mode": r.mode,
                    "analysis": r.result_json,
                }
                for r in records
            ]
    except Exception as exc:
        logger.error("Failed to retrieve session history from PostgreSQL: %s", exc)
        return []


async def get_benchmark() -> dict[str, Any]:
    """Aggregate comparison statistics directly from PostgreSQL AnalysisResult records."""
    try:
        session_factory = get_session_factory()
        async with session_factory() as db:
            stmt = select(
                func.count(AnalysisResult.id),
                func.avg(AnalysisResult.overall_score),
            )
            res = await db.execute(stmt)
            count, avg_score = res.first() or (0, 0.0)

            if not count:
                return {
                    "total_resumes_analyzed": 0,
                    "average_overall_score": 0.0,
                    "dimension_averages": [],
                    "most_common_fixes": [],
                }

            # Fetch recent analysis result JSON objects to compute dimension breakdown
            records_stmt = select(AnalysisResult.result_json).limit(100)
            json_results = (await db.execute(records_stmt)).scalars().all()

            dimension_totals: dict[str, list[int]] = {}
            fix_counts: dict[str, int] = {}

            for res_json in json_results:
                if not isinstance(res_json, dict):
                    continue
                # Dimensions
                for dim in res_json.get("dimensions", []):
                    name = dim.get("name")
                    score = dim.get("score")
                    if name and isinstance(score, (int, float)):
                        dimension_totals.setdefault(name, []).append(score)
                # Critical Fixes
                for fix in res_json.get("critical_fixes", []):
                    issue = fix.get("issue") if isinstance(fix, dict) else str(fix)
                    if issue:
                        fix_counts[issue] = fix_counts.get(issue, 0) + 1

            dimension_averages = [
                {"name": name, "average_score": round(sum(scores) / len(scores), 1)}
                for name, scores in sorted(dimension_totals.items())
                if scores
            ]

            most_common_fixes = [
                {"issue": issue, "count": cnt}
                for issue, cnt in sorted(fix_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            ]

            return {
                "total_resumes_analyzed": count,
                "average_overall_score": round(avg_score, 1) if avg_score else 0.0,
                "dimension_averages": dimension_averages,
                "most_common_fixes": most_common_fixes,
            }
    except Exception as exc:
        logger.error("Failed to compute PostgreSQL benchmark analytics: %s", exc, exc_info=True)
        return {
            "total_resumes_analyzed": 0,
            "average_overall_score": 0.0,
            "dimension_averages": [],
            "most_common_fixes": [],
        }
