#!/usr/bin/env python3
"""USPTO Patent Public Search (PPUBS) MCP server."""

import logging

from ..api_clients.uspto_ppubs_client import USPTOPpubsClient
from ..fastmcp_server import MedicalFastMCP as FastMCP
from ..med_mcp_server import tool as medmcps_tool
from ..med_mcp_server import unified_mcp

logger = logging.getLogger(__name__)

uspto_ppubs_mcp = FastMCP(
    "uspto-ppubs-api-server",
    stateless_http=True,
    json_response=True,
)

# Module-level client so the PPUBS session (and its cookie + access token) are
# reused across requests instead of being re-established on every tool call.
_client = USPTOPpubsClient()


@medmcps_tool(name="uspto_ppubs_search_patents", servers=[uspto_ppubs_mcp, unified_mcp])
async def uspto_ppubs_search_patents(
    query: str,
    offset: int = 0,
    limit: int = 25,
    sort: str = "date_publ desc",
) -> dict:
    """Search granted US patents via USPTO Patent Public Search (ppubs.uspto.gov).

    Args:
        query: USPTO BRS search syntax. Field qualifiers require parentheses around terms.
               Examples: TTL/(drug delivery), ABST/(gene therapy), AN/(Pfizer),
               TTL/(cancer) AND AN/(Novartis), PN/US10000001, CPC/A61K31,
               plain terms like "aspirin" also work for full-text search.
               IMPORTANT: Use TTL/(term) not TTL/"term" — quotes without parens return no results.
        offset: Pagination start position (default 0)
        limit: Max results, up to 500 (default 25)
        sort: Sort order, e.g. "date_publ desc" or "date_publ asc"
    """
    logger.info("Tool invoked: uspto_ppubs_search_patents(query=%s)", query)
    try:
        result = await _client.search_patents(query=query, offset=offset, limit=limit, sort=sort)
        logger.info("Tool succeeded: uspto_ppubs_search_patents")
        return result
    except Exception as e:
        logger.error("Tool failed: uspto_ppubs_search_patents - %s", e, exc_info=True)
        return {"api_source": "USPTO_PPUBS", "data": [], "error": f"USPTO PPUBS error: {e!s}"}


@medmcps_tool(name="uspto_ppubs_search_applications", servers=[uspto_ppubs_mcp, unified_mcp])
async def uspto_ppubs_search_applications(
    query: str,
    offset: int = 0,
    limit: int = 25,
    sort: str = "date_publ desc",
) -> dict:
    """Search published US patent applications (pre-grant) via USPTO PPUBS.

    Applications publish 18 months after filing. Use this to find pending patent
    applications that may not yet be granted.

    Args:
        query: USPTO search syntax (same as uspto_ppubs_search_patents)
        offset: Pagination start position (default 0)
        limit: Max results, up to 500 (default 25)
        sort: Sort order (default "date_publ desc")
    """
    logger.info("Tool invoked: uspto_ppubs_search_applications(query=%s)", query)
    try:
        result = await _client.search_applications(
            query=query, offset=offset, limit=limit, sort=sort
        )
        logger.info("Tool succeeded: uspto_ppubs_search_applications")
        return result
    except Exception as e:
        logger.error("Tool failed: uspto_ppubs_search_applications - %s", e, exc_info=True)
        return {
            "api_source": "USPTO_PPUBS",
            "data": [],
            "error": f"USPTO PPUBS error: {e!s}",
        }
