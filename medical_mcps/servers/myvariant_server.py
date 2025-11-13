#!/usr/bin/env python3
"""
MyVariant.info API MCP Server
Exposes variant annotation tools via MCP at /tools/myvariant/mcp
"""

import logging

from mcp.server.fastmcp import FastMCP

from ..api_clients.myvariant_client import MyVariantClient
from ..med_mcp_server import tool as medmcps_tool
from ..med_mcp_server import unified_mcp

logger = logging.getLogger(__name__)

myvariant_client = MyVariantClient()

myvariant_mcp = FastMCP(
    "myvariant-api-server",
    stateless_http=True,
    json_response=True,
)


@medmcps_tool(name="myvariant_search_variants", servers=[myvariant_mcp, unified_mcp])
async def search_variants(
    gene: str | None = None,
    hgvsp: str | None = None,
    hgvsc: str | None = None,
    rsid: str | None = None,
    significance: str | None = None,
    min_frequency: float | None = None,
    max_frequency: float | None = None,
    cadd_min: float | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """Search genetic variants using MyVariant.info."""
    logger.info(f"Tool invoked: search_variants(gene={gene}, rsid={rsid})")
    try:
        result = await myvariant_client.search_variants(
            gene=gene,
            hgvsp=hgvsp,
            hgvsc=hgvsc,
            rsid=rsid,
            significance=significance,
            min_frequency=min_frequency,
            max_frequency=max_frequency,
            cadd_min=cadd_min,
            limit=limit,
            offset=offset,
        )
        return result
    except Exception as e:
        logger.error(f"Tool failed: search_variants() - {e}", exc_info=True)
        return {"api_source": "MyVariant", "data": [], "error": f"Error: {str(e)}"}


@medmcps_tool(name="myvariant_get_variant", servers=[myvariant_mcp, unified_mcp])
async def get_variant(variant_id: str, include_external: bool = False) -> dict:
    """Get comprehensive variant details by ID."""
    logger.info(f"Tool invoked: get_variant(variant_id='{variant_id}')")
    try:
        result = await myvariant_client.get_variant(
            variant_id, include_external=include_external
        )
        return result
    except Exception as e:
        logger.error(f"Tool failed: get_variant() - {e}", exc_info=True)
        return {"api_source": "MyVariant", "data": None, "error": f"Error: {str(e)}"}
