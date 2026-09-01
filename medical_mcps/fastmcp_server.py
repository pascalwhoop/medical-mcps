"""FastMCP subclass with client-friendly error handling."""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from .errors import client_tool_error_response, unknown_tool_response

logger = logging.getLogger(__name__)


class MedicalFastMCP(FastMCP):
    """Return structured client errors instead of raising for unknown/invalid tool calls."""

    async def call_tool(self, name: str, arguments: dict[str, Any]):
        if self._tool_manager.get_tool(name) is None:
            available = [tool.name for tool in self._tool_manager.list_tools()]
            logger.info("Unknown tool requested: %s", name)
            return unknown_tool_response(name, available)

        try:
            return await super().call_tool(name, arguments)
        except ToolError as exc:
            message = str(exc)
            if "Unknown tool:" in message:
                available = [tool.name for tool in self._tool_manager.list_tools()]
                logger.info("Unknown tool requested: %s", name)
                return unknown_tool_response(name, available)

            if "validation error" in message.lower() or "field required" in message.lower():
                logger.info("Invalid tool arguments for %s: %s", name, message)
                return client_tool_error_response(name, message)

            raise
