#!/usr/bin/env python3
"""Patent API MCP server (FDA-focused v1)."""

import logging

from ..api_clients.patent_client import PatentClient
from ..fastmcp_server import MedicalFastMCP as FastMCP
from ..med_mcp_server import tool as medmcps_tool
from ..med_mcp_server import unified_mcp

logger = logging.getLogger(__name__)

patent_client = PatentClient()  # no network — reads local Orange Book flat files

patent_mcp = FastMCP(
    "patent-api-server",
    stateless_http=True,
    json_response=True,
)


@medmcps_tool(name="patent_search_orange_book", servers=[patent_mcp, unified_mcp])
async def patent_search_orange_book(
    drug_name: str | None = None,
    active_ingredient: str | None = None,
    application_number: str | None = None,
    limit: int = 25,
) -> dict:
    """Search FDA Orange Book-like patent signals via drugs@FDA."""
    logger.info(
        "Tool invoked: patent_search_orange_book(drug_name=%s, active_ingredient=%s, application_number=%s)",
        drug_name,
        active_ingredient,
        application_number,
    )
    try:
        result = await patent_client.patent_search_orange_book(
            drug_name=drug_name,
            active_ingredient=active_ingredient,
            application_number=application_number,
            limit=limit,
        )
        logger.info("Tool succeeded: patent_search_orange_book")
        return result
    except Exception as e:
        logger.error("Tool failed: patent_search_orange_book - %s", e, exc_info=True)
        return {
            "api_source": "FDA_drugsfda",
            "data": [],
            "error": f"Error calling patent API: {e!s}",
        }


@medmcps_tool(name="patent_get_exclusivities", servers=[patent_mcp, unified_mcp])
async def patent_get_exclusivities(
    application_number: str | None = None,
    active_ingredient: str | None = None,
) -> dict:
    """Get non-patent exclusivity records via FDA drugs@FDA."""
    logger.info(
        "Tool invoked: patent_get_exclusivities(application_number=%s, active_ingredient=%s)",
        application_number,
        active_ingredient,
    )
    try:
        result = await patent_client.patent_get_exclusivities(
            application_number=application_number,
            active_ingredient=active_ingredient,
        )
        logger.info("Tool succeeded: patent_get_exclusivities")
        return result
    except Exception as e:
        logger.error("Tool failed: patent_get_exclusivities - %s", e, exc_info=True)
        return {
            "api_source": "FDA_drugsfda",
            "data": [],
            "error": f"Error calling patent API: {e!s}",
        }
