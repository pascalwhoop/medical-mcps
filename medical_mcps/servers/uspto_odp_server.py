#!/usr/bin/env python3
"""USPTO Open Data Portal (ODP) MCP server."""

import logging

from ..api_clients.uspto_odp_client import USPTOOdpClient
from ..fastmcp_server import MedicalFastMCP as FastMCP
from ..med_mcp_server import tool as medmcps_tool
from ..med_mcp_server import unified_mcp

logger = logging.getLogger(__name__)

uspto_odp_mcp = FastMCP(
    "uspto-odp-api-server",
    stateless_http=True,
    json_response=True,
)

_ODP_KEY_MSG = "api_key: USPTO ODP API key (register at https://data.uspto.gov, then 'My ODP')"


@medmcps_tool(name="uspto_odp_get_application", servers=[uspto_odp_mcp, unified_mcp])
async def uspto_odp_get_application(app_num: str, api_key: str = "") -> dict:
    """Get USPTO patent application status and metadata from Open Data Portal.

    Args:
        app_num: Application number — digits only, no slashes (e.g., "14412875")
        api_key: USPTO ODP API key (get from https://data.uspto.gov "My ODP")
    """
    logger.info("Tool invoked: uspto_odp_get_application(app_num=%s)", app_num)
    if not api_key:
        return {
            "error": "api_key is required. Register at https://data.uspto.gov and visit 'My ODP'."
        }
    try:
        client = USPTOOdpClient()
        result = await client.get_application(app_num, api_key=api_key)
        logger.info("Tool succeeded: uspto_odp_get_application")
        return result
    except Exception as e:
        logger.error("Tool failed: uspto_odp_get_application - %s", e, exc_info=True)
        return {"api_source": "USPTO_ODP", "data": None, "error": f"USPTO ODP error: {e!s}"}


@medmcps_tool(name="uspto_odp_get_continuity", servers=[uspto_odp_mcp, unified_mcp])
async def uspto_odp_get_continuity(app_num: str, api_key: str = "") -> dict:
    """Get patent family / continuity data for an application (parent/child apps, CIPs, divisionals).

    Args:
        app_num: Application number — digits only, no slashes (e.g., "14412875")
        api_key: USPTO ODP API key (get from https://data.uspto.gov "My ODP")
    """
    logger.info("Tool invoked: uspto_odp_get_continuity(app_num=%s)", app_num)
    if not api_key:
        return {
            "error": "api_key is required. Register at https://data.uspto.gov and visit 'My ODP'."
        }
    try:
        client = USPTOOdpClient()
        result = await client.get_continuity(app_num, api_key=api_key)
        logger.info("Tool succeeded: uspto_odp_get_continuity")
        return result
    except Exception as e:
        logger.error("Tool failed: uspto_odp_get_continuity - %s", e, exc_info=True)
        return {"api_source": "USPTO_ODP", "data": None, "error": f"USPTO ODP error: {e!s}"}


@medmcps_tool(name="uspto_odp_get_assignment", servers=[uspto_odp_mcp, unified_mcp])
async def uspto_odp_get_assignment(app_num: str, api_key: str = "") -> dict:
    """Get patent ownership / assignment records for an application.

    Args:
        app_num: Application number — digits only, no slashes (e.g., "14412875")
        api_key: USPTO ODP API key (get from https://data.uspto.gov "My ODP")
    """
    logger.info("Tool invoked: uspto_odp_get_assignment(app_num=%s)", app_num)
    if not api_key:
        return {
            "error": "api_key is required. Register at https://data.uspto.gov and visit 'My ODP'."
        }
    try:
        client = USPTOOdpClient()
        result = await client.get_assignment(app_num, api_key=api_key)
        logger.info("Tool succeeded: uspto_odp_get_assignment")
        return result
    except Exception as e:
        logger.error("Tool failed: uspto_odp_get_assignment - %s", e, exc_info=True)
        return {"api_source": "USPTO_ODP", "data": None, "error": f"USPTO ODP error: {e!s}"}


@medmcps_tool(name="uspto_odp_get_transactions", servers=[uspto_odp_mcp, unified_mcp])
async def uspto_odp_get_transactions(app_num: str, api_key: str = "") -> dict:
    """Get prosecution history / transaction records for a patent application.

    Args:
        app_num: Application number — digits only, no slashes (e.g., "14412875")
        api_key: USPTO ODP API key (get from https://data.uspto.gov "My ODP")
    """
    logger.info("Tool invoked: uspto_odp_get_transactions(app_num=%s)", app_num)
    if not api_key:
        return {
            "error": "api_key is required. Register at https://data.uspto.gov and visit 'My ODP'."
        }
    try:
        client = USPTOOdpClient()
        result = await client.get_transactions(app_num, api_key=api_key)
        logger.info("Tool succeeded: uspto_odp_get_transactions")
        return result
    except Exception as e:
        logger.error("Tool failed: uspto_odp_get_transactions - %s", e, exc_info=True)
        return {"api_source": "USPTO_ODP", "data": None, "error": f"USPTO ODP error: {e!s}"}


@medmcps_tool(name="uspto_odp_search_applications", servers=[uspto_odp_mcp, unified_mcp])
async def uspto_odp_search_applications(
    assignee_name: str | None = None,
    inventor_name: str | None = None,
    patent_number: str | None = None,
    application_number: str | None = None,
    filing_date_from: str | None = None,
    filing_date_to: str | None = None,
    offset: int = 0,
    limit: int = 25,
    api_key: str = "",
) -> dict:
    """Search USPTO patent applications by assignee, inventor, number, or date range.

    Args:
        assignee_name: Filter by assignee/applicant name (partial match)
        inventor_name: Filter by inventor name
        patent_number: Filter by granted patent number
        application_number: Filter by application number (digits only)
        filing_date_from: Filing date range start (YYYY-MM-DD)
        filing_date_to: Filing date range end (YYYY-MM-DD)
        offset: Pagination start (default 0)
        limit: Max results (default 25)
        api_key: USPTO ODP API key (get from https://data.uspto.gov "My ODP")
    """
    logger.info(
        "Tool invoked: uspto_odp_search_applications(assignee=%s, inventor=%s)",
        assignee_name,
        inventor_name,
    )
    if not api_key:
        return {
            "error": "api_key is required. Register at https://data.uspto.gov and visit 'My ODP'."
        }
    try:
        client = USPTOOdpClient()
        result = await client.search_applications(
            assignee_name=assignee_name,
            inventor_name=inventor_name,
            patent_number=patent_number,
            application_number=application_number,
            filing_date_from=filing_date_from,
            filing_date_to=filing_date_to,
            offset=offset,
            limit=limit,
            api_key=api_key,
        )
        logger.info("Tool succeeded: uspto_odp_search_applications")
        return result
    except Exception as e:
        logger.error("Tool failed: uspto_odp_search_applications - %s", e, exc_info=True)
        return {"api_source": "USPTO_ODP", "data": None, "error": f"USPTO ODP error: {e!s}"}
