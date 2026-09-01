"""Tests for MedicalFastMCP client-error handling."""

from unittest.mock import patch

import pytest

from medical_mcps.errors import CLIENT_ERROR_TYPE
from medical_mcps.fastmcp_server import MedicalFastMCP


@pytest.mark.asyncio
async def test_unknown_tool_returns_client_error_envelope():
    server = MedicalFastMCP("test-server", stateless_http=True, json_response=True)

    @server.tool()
    async def existing_tool() -> dict:
        return {"ok": True}

    result = await server.call_tool("opentargets_get_target", {})
    assert result["metadata"]["error_type"] == CLIENT_ERROR_TYPE
    assert "opentargets_get_target" in result["metadata"]["error"]
    assert "existing_tool" not in result["metadata"].get("suggestions", [])


@pytest.mark.asyncio
@patch("medical_mcps.fastmcp_server.log_tool_call")
async def test_unknown_tool_logs_usage(mock_log_tool_call):
    server = MedicalFastMCP("test-server", stateless_http=True, json_response=True)

    @server.tool()
    async def existing_tool() -> dict:
        return {"ok": True}

    await server.call_tool("opentargets_get_target", {"gene": "BRAF"})

    mock_log_tool_call.assert_called_once()
    kwargs = mock_log_tool_call.call_args.kwargs
    assert kwargs["tool"] == "opentargets_get_target"
    assert kwargs["arguments"] == {"gene": "BRAF"}
    assert kwargs["outcome"] == "unknown_tool"
    assert kwargs["error_type"] == CLIENT_ERROR_TYPE
    assert kwargs["latency_ms"] is not None


@pytest.mark.asyncio
@patch("medical_mcps.fastmcp_server.log_tool_call")
async def test_successful_tool_logs_usage(mock_log_tool_call):
    server = MedicalFastMCP("test-server", stateless_http=True, json_response=True)

    @server.tool()
    async def existing_tool() -> dict:
        return {"api_source": "test", "data": {"ok": True}, "metadata": {}}

    await server.call_tool("existing_tool", {})

    mock_log_tool_call.assert_called_once()
    kwargs = mock_log_tool_call.call_args.kwargs
    assert kwargs["tool"] == "existing_tool"
    assert kwargs["outcome"] == "ok"
    assert kwargs["error_type"] is None
