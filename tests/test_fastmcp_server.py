"""Tests for MedicalFastMCP client-error handling."""

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
