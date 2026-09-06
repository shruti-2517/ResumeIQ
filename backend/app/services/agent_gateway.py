"""Multi-Agent Supervisor Orchestrator & Tool Logging Gateway."""

import logging
import time
from datetime import datetime, timezone
from importlib import import_module
from typing import Any

logger = logging.getLogger(__name__)


class AgentServiceUnavailable(RuntimeError):
    """Raised when the separately supplied agent service cannot be called."""


AGENT_NAME_MAP = {
    "analyze": "Resume Auditor Agent",
    "company_analyze": "Company Analyst Agent",
    "rewrite": "Resume Rewriter Agent",
    "roadmap": "Career Coach Agent",
    "get_benchmark": "Benchmarking Agent",
    "save_to_mongo": "Persistence Agent",
    "get_history": "Persistence Agent",
    "export_to_drive": "Export Agent",
}

# Global in-memory tool call audit trail
_TOOL_EXECUTION_LOGS: list[dict[str, Any]] = []
_SUPERVISOR_METRICS: dict[str, Any] = {
    "total_agent_invocations": 0,
    "successful_invocations": 0,
    "failed_invocations": 0,
    "last_active_agent": None,
    "last_invocation_timestamp": None,
}


def log_tool_execution(
    agent_name: str,
    tool_name: str,
    tool_args: dict[str, Any],
    execution_time_ms: float,
    status: str = "success",
    error_message: str | None = None,
) -> dict[str, Any]:
    """Record an agent tool execution event in the central gateway audit trail."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_name": agent_name,
        "tool_name": tool_name,
        "tool_args": {k: str(v)[:100] for k, v in tool_args.items()} if isinstance(tool_args, dict) else {},
        "execution_time_ms": round(execution_time_ms, 2),
        "status": status,
        "error_message": error_message,
    }
    _TOOL_EXECUTION_LOGS.append(entry)
    if len(_TOOL_EXECUTION_LOGS) > 500:
        _TOOL_EXECUTION_LOGS.pop(0)
    logger.info("Supervisor logged tool execution: [%s] %s -> %s (%s ms)", agent_name, tool_name, status, round(execution_time_ms, 2))
    return entry


def get_tool_logs(limit: int = 50) -> list[dict[str, Any]]:
    """Retrieve recent agent tool execution logs from the supervisor gateway."""
    return list(reversed(_TOOL_EXECUTION_LOGS[-limit:]))


def clear_tool_logs() -> None:
    """Clear supervisor tool execution logs (for testing)."""
    _TOOL_EXECUTION_LOGS.clear()


def get_supervisor_state() -> dict[str, Any]:
    """Get current multi-agent supervisor metrics and active pipeline state."""
    return {
        "supervisor_status": "ONLINE",
        "metrics": dict(_SUPERVISOR_METRICS),
        "total_tool_calls_logged": len(_TOOL_EXECUTION_LOGS),
        "registered_agents": list(set(AGENT_NAME_MAP.values())),
    }


def _agent_function(name: str):
    try:
        module = import_module("app.services.agent")
    except ImportError as exc:
        raise AgentServiceUnavailable(
            "Agent service package app.services.agent is not installed"
        ) from exc

    function = getattr(module, name, None)
    if not callable(function):
        raise AgentServiceUnavailable(f"Agent service function {name}() is not available")
    return function


async def invoke(name: str, **kwargs: Any) -> Any:
    """Invoke an autonomous agent function via the Supervisor Orchestrator Gateway with tool logging."""
    agent_name = AGENT_NAME_MAP.get(name, f"Agent ({name})")
    start_time = time.perf_counter()

    _SUPERVISOR_METRICS["total_agent_invocations"] += 1
    _SUPERVISOR_METRICS["last_active_agent"] = agent_name
    _SUPERVISOR_METRICS["last_invocation_timestamp"] = datetime.now(timezone.utc).isoformat()

    logger.info("Supervisor Gateway dispatching invocation to '%s' (function: %s)", agent_name, name)

    try:
        func = _agent_function(name)
        result = await func(**kwargs)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        _SUPERVISOR_METRICS["successful_invocations"] += 1

        # Record high-level supervisor log entry
        log_tool_execution(
            agent_name=agent_name,
            tool_name=f"invoke_{name}",
            tool_args={"kwargs_keys": list(kwargs.keys())},
            execution_time_ms=elapsed_ms,
            status="success",
        )

        # Attach supervisor execution metadata to dict results
        if isinstance(result, dict) and "error" not in result:
            result["_supervisor_telemetry"] = {
                "agent_name": agent_name,
                "execution_time_ms": round(elapsed_ms, 2),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        return result

    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        _SUPERVISOR_METRICS["failed_invocations"] += 1

        log_tool_execution(
            agent_name=agent_name,
            tool_name=f"invoke_{name}",
            tool_args={"kwargs_keys": list(kwargs.keys())},
            execution_time_ms=elapsed_ms,
            status="failed",
            error_message=str(exc),
        )
        logger.error("Supervisor Gateway error invoking '%s': %s", agent_name, exc, exc_info=True)
        raise
