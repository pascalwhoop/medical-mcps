"""
Test FastMCP/Starlette HTTP layer isolation

This test verifies that the FastMCP/Starlette HTTP layer works correctly
when tested in isolation, ensuring the HTTP transport layer functions properly.
"""

import time

import httpx
import pytest
from httpx import ASGITransport

from medical_mcps.servers.biothings_server import biothings_mcp


@pytest.mark.asyncio
async def test_biothings_fastmcp_isolation():
    """Test BioThings FastMCP server HTTP layer in isolation"""
    # Use the streamable_http_app directly (it returns a Starlette app)
    app = biothings_mcp.streamable_http_app()

    # Start session manager and run app in async context
    async with biothings_mcp.session_manager.run():
        # Use httpx.AsyncClient with ASGI transport
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            # Try root path first
            request_data = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "mygene_get_gene",
                    "arguments": {"gene_id_or_symbol": "TP53"},
                },
            }

            # Use /mcp path with proper headers (like Tavern tests do)
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            }

            start = time.time()
            response = await client.post(
                "/mcp", json=request_data, headers=headers, timeout=30.0
            )
            elapsed = time.time() - start

            print(f"Request took {elapsed:.2f}s, status={response.status_code}")
            if response.status_code != 200:
                print(f"Response: {response.text[:200]}")

            assert response.status_code == 200
            assert elapsed < 10.0  # Should complete quickly
