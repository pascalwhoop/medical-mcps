#!/usr/bin/env python3
"""
ClinicalTrials.gov API MCP Server
Exposes ClinicalTrials.gov API tools via MCP at /tools/ctg/mcp
"""

import logging

from mcp.server.fastmcp import FastMCP
from ..med_mcp_server import unified_mcp, tool as medmcps_tool

from ..api_clients.ctg_client import CTGClient

logger = logging.getLogger(__name__)

# Initialize API client
ctg_client = CTGClient()

# Create FastMCP server for ClinicalTrials.gov
ctg_mcp = FastMCP(
    "ctg-api-server",
    stateless_http=True,
    json_response=True,
)


@medmcps_tool(name="ctg_search_studies", servers=[ctg_mcp, unified_mcp])
async def search_studies(
    condition: str = None,
    intervention: str = None,
    status: str = None,
    page_size: int = 20,
) -> dict:
    """Search clinical trials from ClinicalTrials.gov.

    IMPORTANT: Provide at least one of 'condition' or 'intervention' to narrow results.
    Status should be a comma-separated list (e.g., 'RECRUITING,COMPLETED').

    Args:
        condition: Condition/disease query (e.g., 'multiple sclerosis')
        intervention: Intervention/treatment query (e.g., 'ocrelizumab')
        status: Comma-separated list of statuses (e.g., 'RECRUITING,COMPLETED'). 
                Common values: RECRUITING, NOT_YET_RECRUITING, COMPLETED, TERMINATED, SUSPENDED
        page_size: Number of results per page (default: 20, max recommended: 100)

    Returns:
        JSON with study results and pagination info (use nextPageToken for next page)
    """
    logger.info(
        f"Tool invoked: search_studies(condition='{condition}', intervention='{intervention}', status='{status}', page_size={page_size})"
    )

    # Parse status if provided
    status_list = None
    if status:
        status_list = [s.strip() for s in status.split(",") if s.strip()]

    try:
        result = await ctg_client.search_studies(
            condition=condition,
            intervention=intervention,
            status=status_list,
            page_size=page_size,
        )
        logger.info("Tool succeeded: search_studies()")
        return result
    except Exception as e:
        logger.error(f"Tool failed: search_studies() - {e}", exc_info=True)
        return f"Error calling ClinicalTrials.gov API: {str(e)}"


@medmcps_tool(name="ctg_get_study", servers=[ctg_mcp, unified_mcp])
async def get_study(nct_id: str) -> dict:
    """Get single clinical trial study by NCT ID.

    IMPORTANT: NCT ID format is 'NCT' followed by 8 digits (e.g., 'NCT00841061').

    Args:
        nct_id: NCT identifier (e.g., 'NCT00841061')

    Returns:
        JSON with complete study data including conditions, interventions, outcomes, and eligibility
    """
    logger.info(f"Tool invoked: get_study(nct_id='{nct_id}')")
    try:
        result = await ctg_client.get_study(nct_id)
        logger.info(f"Tool succeeded: get_study(nct_id='{nct_id}')")
        return result
    except Exception as e:
        logger.error(f"Tool failed: get_study(nct_id='{nct_id}') - {e}", exc_info=True)
        return f"Error calling ClinicalTrials.gov API: {str(e)}"


@medmcps_tool(name="ctg_search_by_condition", servers=[ctg_mcp, unified_mcp])
async def search_by_condition(
    condition_query: str, status: str = None, page_size: int = 20
) -> dict:
    """Search clinical trials by condition/disease.

    Args:
        condition_query: Condition or disease name (e.g., 'multiple sclerosis')
        status: Comma-separated list of statuses to filter (optional)
        page_size: Number of results per page (default: 20)

    Returns:
        JSON with study results matching the condition
    """
    logger.info(
        f"Tool invoked: search_by_condition(condition_query='{condition_query}', status='{status}', page_size={page_size})"
    )

    # Parse status if provided
    status_list = None
    if status:
        status_list = [s.strip() for s in status.split(",") if s.strip()]

    try:
        result = await ctg_client.search_by_condition(
            condition_query, status=status_list, page_size=page_size
        )
        logger.info(f"Tool succeeded: search_by_condition(condition_query='{condition_query}')")
        return result
    except Exception as e:
        logger.error(
            f"Tool failed: search_by_condition(condition_query='{condition_query}') - {e}",
            exc_info=True,
        )
        return f"Error calling ClinicalTrials.gov API: {str(e)}"


@medmcps_tool(name="ctg_search_by_intervention", servers=[ctg_mcp, unified_mcp])
async def search_by_intervention(
    intervention_query: str, status: str = None, page_size: int = 20
) -> dict:
    """Search clinical trials by intervention/treatment.

    Args:
        intervention_query: Intervention or treatment name (e.g., 'ocrelizumab')
        status: Comma-separated list of statuses to filter (optional)
        page_size: Number of results per page (default: 20)

    Returns:
        JSON with study results matching the intervention
    """
    logger.info(
        f"Tool invoked: search_by_intervention(intervention_query='{intervention_query}', status='{status}', page_size={page_size})"
    )

    # Parse status if provided
    status_list = None
    if status:
        status_list = [s.strip() for s in status.split(",") if s.strip()]

    try:
        result = await ctg_client.search_by_intervention(
            intervention_query, status=status_list, page_size=page_size
        )
        logger.info(
            f"Tool succeeded: search_by_intervention(intervention_query='{intervention_query}')"
        )
        return result
    except Exception as e:
        logger.error(
            f"Tool failed: search_by_intervention(intervention_query='{intervention_query}') - {e}",
            exc_info=True,
        )
        return f"Error calling ClinicalTrials.gov API: {str(e)}"


@medmcps_tool(name="ctg_get_study_metadata", servers=[ctg_mcp, unified_mcp])
async def get_study_metadata() -> dict:
    """Get ClinicalTrials.gov data model metadata (available fields).

    Returns:
        JSON with field metadata including field names, types, and descriptions
    """
    logger.info("Tool invoked: get_study_metadata()")
    try:
        result = await ctg_client.get_study_metadata()
        logger.info("Tool succeeded: get_study_metadata()")
        return result
    except Exception as e:
        logger.error(f"Tool failed: get_study_metadata() - {e}", exc_info=True)
        return f"Error calling ClinicalTrials.gov API: {str(e)}"

