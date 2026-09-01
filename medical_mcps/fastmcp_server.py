"""FastMCP subclass with client-friendly error handling."""

from __future__ import annotations

import logging
import time
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from .errors import (
    CLIENT_ERROR_TYPE,
    UPSTREAM_ERROR_TYPE,
    client_tool_error_response,
    unknown_tool_response,
)
from .usage_logging import log_tool_call

logger = logging.getLogger(__name__)


def _outcome_from_result(result: Any) -> tuple[str, str | None]:
    if not isinstance(result, dict):
        return "ok", None

    metadata = result.get("metadata")
    if not isinstance(metadata, dict):
        return "ok", None

    error_type = metadata.get("error_type")
    if error_type == CLIENT_ERROR_TYPE:
        return "client_error", error_type
    if error_type == UPSTREAM_ERROR_TYPE:
        return "upstream_error", error_type
    if metadata.get("error"):
        return "error", error_type
    return "ok", None


class MedicalFastMCP(FastMCP):
    """Return structured client errors instead of raising for unknown/invalid tool calls."""

    async def call_tool(self, name: str, arguments: dict[str, Any]):
        start = time.perf_counter()

        def record(outcome: str, error_type: str | None = None) -> None:
            log_tool_call(
                tool=name,
                arguments=arguments,
                outcome=outcome,
                error_type=error_type,
                latency_ms=round((time.perf_counter() - start) * 1000, 1),
            )

        if self._tool_manager.get_tool(name) is None:
            available = [tool.name for tool in self._tool_manager.list_tools()]
            logger.info("Unknown tool requested: %s", name)
            record("unknown_tool", CLIENT_ERROR_TYPE)
            return unknown_tool_response(name, available)

        try:
            result = await super().call_tool(name, arguments)
        except ToolError as exc:
            message = str(exc)
            if "Unknown tool:" in message:
                available = [tool.name for tool in self._tool_manager.list_tools()]
                logger.info("Unknown tool requested: %s", name)
                record("unknown_tool", CLIENT_ERROR_TYPE)
                return unknown_tool_response(name, available)

            if "validation error" in message.lower() or "field required" in message.lower():
                logger.info("Invalid tool arguments for %s: %s", name, message)
                record("validation_error", CLIENT_ERROR_TYPE)
                return client_tool_error_response(name, message)

            record("error", None)
            raise

        outcome, error_type = _outcome_from_result(result)
        record(outcome, error_type)
        return result
