"""Structured usage events for Cloud Logging → BigQuery analytics."""

from __future__ import annotations

import json
import sys
from typing import Any

USAGE_EVENT = "tool_call"


def log_tool_call(
    *,
    tool: str,
    arguments: dict[str, Any],
    outcome: str,
    latency_ms: float | None = None,
    error_type: str | None = None,
) -> None:
    """Emit one JSON line to stdout for Cloud Logging / BigQuery export."""
    payload: dict[str, Any] = {
        "severity": "INFO",
        "event": USAGE_EVENT,
        "tool": tool,
        "args_keys": sorted(arguments.keys()),
        "arg_count": len(arguments),
        "outcome": outcome,
    }
    if latency_ms is not None:
        payload["latency_ms"] = latency_ms
    if error_type is not None:
        payload["error_type"] = error_type

    sys.stdout.write(json.dumps(payload, separators=(",", ":")) + "\n")
    sys.stdout.flush()
