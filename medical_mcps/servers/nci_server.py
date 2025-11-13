#!/usr/bin/env python3
"""
NCI Clinical Trials Search API MCP Server
Exposes NCI trial search tools via MCP at /tools/nci/mcp
"""

import logging
import os

from mcp.server.fastmcp import FastMCP
from ..med_mcp_server import unified_mcp, tool as medmcps_tool

from ..api_clients.nci_client import NCIClient

logger = logging.getLogger(__name__)

# Initialize API client with API key from env var
nci_client = NCIClient(api_key=os.getenv("NCI_API_KEY"))

nci_mcp = FastMCP(
    "nci-api-server",
    stateless_http=True,
    json_response=True,
)


@medmcps_tool(name="nci_search_trials", servers=[nci_mcp, unified_mcp])
async def search_trials(
    conditions: list[str] | None = None,
    interventions: list[str] | None = None,
    phase: str | None = None,
    status: str | None = None,
    limit: int = 20,
    offset: int = 0,
    api_key: str | None = None,
) -> dict:
    """Search NCI clinical trials for cancer research.

    Args:
        conditions: List of condition/disease names (e.g., ['melanoma'])
        interventions: List of intervention names (e.g., ['pembrolizumab'])
        phase: Trial phase filter (e.g., 'PHASE1', 'PHASE2', 'PHASE3')
        status: Recruiting status filter
        limit: Maximum number of results (default: 20)
        offset: Result offset for pagination (default: 0)
        api_key: Optional NCI API key (overrides NCI_API_KEY env var)

    Returns:
        JSON with list of matching clinical trials
    """
    logger.info(
        f"Tool invoked: nci_search_trials(conditions={conditions}, interventions={interventions})"
    )
    try:
        # Use provided API key or existing client
        if api_key:
            client = NCIClient(api_key=api_key)
        else:
            client = nci_client

        result = await client.search_trials(
            conditions=conditions,
            interventions=interventions,
            phase=phase,
            status=status,
            limit=limit,
            offset=offset,
        )
        return result
    except Exception as e:
        logger.error(f"Tool failed: nci_search_trials() - {e}", exc_info=True)
        return {"api_source": "NCI", "data": [], "error": f"Error: {str(e)}"}


@medmcps_tool(name="nci_get_trial", servers=[nci_mcp, unified_mcp])
async def get_trial(trial_id: str, api_key: str | None = None) -> dict:
    """Get NCI trial details by ID.

    Args:
        trial_id: NCI trial ID
        api_key: Optional NCI API key (overrides NCI_API_KEY env var)

    Returns:
        JSON with detailed trial information
    """
    logger.info(f"Tool invoked: nci_get_trial(trial_id='{trial_id}')")
    try:
        # Use provided API key or existing client
        if api_key:
            client = NCIClient(api_key=api_key)
        else:
            client = nci_client

        result = await client.get_trial(trial_id)
        return result
    except Exception as e:
        logger.error(f"Tool failed: nci_get_trial() - {e}", exc_info=True)
        return {"api_source": "NCI", "data": None, "error": f"Error: {str(e)}"}
