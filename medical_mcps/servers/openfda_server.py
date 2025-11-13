#!/usr/bin/env python3
"""
OpenFDA API MCP Server
Exposes OpenFDA tools via MCP at /tools/openfda/mcp
"""

import logging

from mcp.server.fastmcp import FastMCP
from ..med_mcp_server import unified_mcp, tool as medmcps_tool

from ..api_clients.openfda_client import OpenFDAClient

logger = logging.getLogger(__name__)

# Initialize API client
openfda_client = OpenFDAClient()

# Create FastMCP server for OpenFDA
openfda_mcp = FastMCP(
    "openfda-api-server",
    stateless_http=True,
    json_response=True,
)


@medmcps_tool(name="openfda_search_adverse_events", servers=[openfda_mcp, unified_mcp])
async def search_adverse_events(
    drug: str | None = None,
    reaction: str | None = None,
    serious: bool | None = None,
    limit: int = 25,
    page: int = 1,
    api_key: str | None = None,
) -> dict:
    """Search FDA adverse event reports (FAERS).

    Args:
        drug: Drug name to search for (e.g., 'ocrelizumab')
        reaction: Adverse reaction term to search for (e.g., 'nausea')
        serious: Filter for serious events only (True/False)
        limit: Maximum number of results per page (default: 25, max: 100)
        page: Page number (1-based, default: 1)
        api_key: Optional OpenFDA API key (for higher rate limits)

    Returns:
        JSON with list of adverse event reports including safety report ID, drugs, reactions, and metadata
    """
    logger.info(
        f"Tool invoked: search_adverse_events(drug={drug}, reaction={reaction}, serious={serious}, limit={limit}, page={page})"
    )
    try:
        result = await openfda_client.search_adverse_events(
            drug=drug,
            reaction=reaction,
            serious=serious,
            limit=limit,
            page=page,
            api_key=api_key,
        )
        logger.info("Tool succeeded: search_adverse_events()")
        return result
    except Exception as e:
        logger.error(f"Tool failed: search_adverse_events() - {e}", exc_info=True)
        return {
            "api_source": "OpenFDA",
            "data": [],
            "error": f"Error calling OpenFDA API: {str(e)}",
        }


@medmcps_tool(name="openfda_get_adverse_event", servers=[openfda_mcp, unified_mcp])
async def get_adverse_event(report_id: str, api_key: str | None = None) -> dict:
    """Get detailed adverse event report by safety report ID.

    Args:
        report_id: Safety report ID
        api_key: Optional OpenFDA API key

    Returns:
        JSON with detailed report information including patient data, drugs, reactions, and summary
    """
    logger.info(f"Tool invoked: get_adverse_event(report_id='{report_id}')")
    try:
        result = await openfda_client.get_adverse_event(report_id, api_key=api_key)
        logger.info(f"Tool succeeded: get_adverse_event(report_id='{report_id}')")
        return result
    except Exception as e:
        logger.error(
            f"Tool failed: get_adverse_event(report_id='{report_id}') - {e}",
            exc_info=True,
        )
        return {
            "api_source": "OpenFDA",
            "data": None,
            "error": f"Error calling OpenFDA API: {str(e)}",
        }


@medmcps_tool(name="openfda_search_drug_labels", servers=[openfda_mcp, unified_mcp])
async def search_drug_labels(
    drug_name: str | None = None,
    indication: str | None = None,
    section: str | None = None,
    limit: int = 25,
    page: int = 1,
    api_key: str | None = None,
) -> dict:
    """Search FDA drug product labels (SPL).

    Args:
        drug_name: Drug name to search for (e.g., 'ocrelizumab')
        indication: Search for drugs indicated for this condition (e.g., 'multiple sclerosis')
        section: Specific label section to search (e.g., 'warnings_and_precautions')
        limit: Maximum number of results per page (default: 25, max: 100)
        page: Page number (1-based, default: 1)
        api_key: Optional OpenFDA API key

    Returns:
        JSON with list of drug labels matching criteria
    """
    logger.info(
        f"Tool invoked: search_drug_labels(drug_name={drug_name}, indication={indication}, section={section}, limit={limit}, page={page})"
    )
    try:
        result = await openfda_client.search_drug_labels(
            drug_name=drug_name,
            indication=indication,
            section=section,
            limit=limit,
            page=page,
            api_key=api_key,
        )
        logger.info("Tool succeeded: search_drug_labels()")
        return result
    except Exception as e:
        logger.error(f"Tool failed: search_drug_labels() - {e}", exc_info=True)
        return {
            "api_source": "OpenFDA",
            "data": [],
            "error": f"Error calling OpenFDA API: {str(e)}",
        }


@medmcps_tool(name="openfda_get_drug_label", servers=[openfda_mcp, unified_mcp])
async def get_drug_label(
    set_id: str, sections: list[str] | None = None, api_key: str | None = None
) -> dict:
    """Get full drug label by set ID.

    Args:
        set_id: Label set ID
        sections: Specific sections to retrieve (optional, e.g., ['indications_and_usage', 'adverse_reactions'])
        api_key: Optional OpenFDA API key

    Returns:
        JSON with full prescribing information including requested sections
    """
    logger.info(f"Tool invoked: get_drug_label(set_id='{set_id}', sections={sections})")
    try:
        result = await openfda_client.get_drug_label(
            set_id, sections=sections, api_key=api_key
        )
        logger.info(f"Tool succeeded: get_drug_label(set_id='{set_id}')")
        return result
    except Exception as e:
        logger.error(
            f"Tool failed: get_drug_label(set_id='{set_id}') - {e}",
            exc_info=True,
        )
        return {
            "api_source": "OpenFDA",
            "data": None,
            "error": f"Error calling OpenFDA API: {str(e)}",
        }


@medmcps_tool(name="openfda_search_device_events", servers=[openfda_mcp, unified_mcp])
async def search_device_events(
    device: str | None = None,
    manufacturer: str | None = None,
    problem: str | None = None,
    limit: int = 25,
    page: int = 1,
    api_key: str | None = None,
) -> dict:
    """Search FDA device adverse event reports (MAUDE).

    Args:
        device: Device name to search for
        manufacturer: Manufacturer name
        problem: Device problem description
        limit: Maximum number of results per page (default: 25, max: 100)
        page: Page number (1-based, default: 1)
        api_key: Optional OpenFDA API key

    Returns:
        JSON with list of device adverse event reports
    """
    logger.info(
        f"Tool invoked: search_device_events(device={device}, manufacturer={manufacturer}, problem={problem}, limit={limit}, page={page})"
    )
    try:
        result = await openfda_client.search_device_events(
            device=device,
            manufacturer=manufacturer,
            problem=problem,
            limit=limit,
            page=page,
            api_key=api_key,
        )
        logger.info("Tool succeeded: search_device_events()")
        return result
    except Exception as e:
        logger.error(f"Tool failed: search_device_events() - {e}", exc_info=True)
        return {
            "api_source": "OpenFDA",
            "data": [],
            "error": f"Error calling OpenFDA API: {str(e)}",
        }
