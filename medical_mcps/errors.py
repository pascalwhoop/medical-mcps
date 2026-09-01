"""Shared client-facing error envelopes for MCP tools and API clients."""

from __future__ import annotations

from difflib import get_close_matches
from typing import Any

CLIENT_ERROR_TYPE = "client_error"
UPSTREAM_ERROR_TYPE = "upstream_error"


def suggest_tools(name: str, available: list[str], limit: int = 5) -> list[str]:
    """Return tool names that may match a hallucinated tool name."""
    if not available:
        return []

    prefix = name.split("_", 1)[0] if "_" in name else name
    prefix_matches = [tool for tool in available if tool.startswith(f"{prefix}_")]
    close_matches = get_close_matches(name, available, n=limit, cutoff=0.5)
    suggestions: list[str] = []
    for candidate in prefix_matches + close_matches:
        if candidate not in suggestions:
            suggestions.append(candidate)
        if len(suggestions) >= limit:
            break
    return suggestions


def unknown_tool_response(tool_name: str, available: list[str]) -> dict[str, Any]:
    suggestions = suggest_tools(tool_name, available)
    metadata: dict[str, Any] = {
        "error": f"Unknown tool: {tool_name}",
        "error_type": CLIENT_ERROR_TYPE,
        "message": "This tool does not exist on this server. Call tools/list for valid names.",
    }
    if suggestions:
        metadata["suggestions"] = suggestions
    return {
        "api_source": "medical-mcps",
        "data": None,
        "metadata": metadata,
    }


def client_tool_error_response(tool_name: str, detail: str) -> dict[str, Any]:
    return {
        "api_source": "medical-mcps",
        "data": None,
        "metadata": {
            "error": f"Invalid request for tool {tool_name}",
            "error_type": CLIENT_ERROR_TYPE,
            "message": detail,
        },
    }


def upstream_error_metadata(
    *,
    api_name: str,
    detail: str,
    status_code: int | None = None,
) -> dict[str, Any]:
    return {
        "error": f"Upstream service error: {api_name}",
        "error_type": UPSTREAM_ERROR_TYPE,
        "message": (
            "An upstream data source returned an error. "
            "This is not a bug in medical-mcps; retry later or use an alternate source."
        ),
        "upstream_api": api_name,
        "upstream_status": status_code,
        "upstream_detail": detail,
    }


def upstream_error_response(
    *,
    api_name: str,
    detail: str,
    status_code: int | None = None,
    data: Any = None,
) -> dict[str, Any]:
    return {
        "api_source": api_name,
        "data": data,
        "metadata": upstream_error_metadata(
            api_name=api_name,
            detail=detail,
            status_code=status_code,
        ),
    }


def is_transient_neo4j_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return any(
        token in message
        for token in (
            "defunct",
            "connection reset",
            "sessionexpired",
            "routing information",
            "failed to read",
            "failed to write",
            "serviceunavailable",
        )
    )
