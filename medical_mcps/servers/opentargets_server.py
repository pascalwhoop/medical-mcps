#!/usr/bin/env python3
"""OpenTargets MCP Server."""

import logging

from mcp.server.fastmcp import FastMCP

from ..api_clients.opentargets_client import OpenTargetsClient
from ..med_mcp_server import tool as medmcps_tool
from ..med_mcp_server import unified_mcp
from ..models.opentargets import OpenTargetsAssociation
from .validation import validate_response, validate_list_response

logger = logging.getLogger(__name__)

opentargets_client = OpenTargetsClient()

opentargets_mcp = FastMCP(
    "opentargets-api-server",
    stateless_http=True,
    json_response=True,
)


@medmcps_tool(name="opentargets_search", servers=[opentargets_mcp, unified_mcp])
async def opentargets_search(
    query: str, entity: str | None = None, size: int = 10
) -> dict:
    """Search OpenTargets entities (targets, diseases, drugs)."""
    logger.info(
        "Tool invoked: opentargets_search(query='%s', entity='%s', size=%s)",
        query,
        entity,
        size,
    )
    try:
        result = await opentargets_client.search(query=query, entity=entity, size=size)
        # OpenTargets returns {"data": [...]} structure
        if isinstance(result, dict) and "data" in result and isinstance(result["data"], list):
            result = validate_list_response(
                result,
                OpenTargetsAssociation,
                list_key="data",
                api_name="OpenTargets",
            )
        return result
    except Exception as e:  # pragma: no cover - defensive
        logger.error("Tool failed: opentargets_search() - %s", e, exc_info=True)
        return {"api_source": "OpenTargets", "data": None, "error": str(e)}


@medmcps_tool(
    name="opentargets_get_associations", servers=[opentargets_mcp, unified_mcp]
)
async def opentargets_get_associations(
    target_id: str | None = None,
    disease_id: str | None = None,
    size: int = 50,
) -> dict:
    """Get target-disease associations from OpenTargets."""
    logger.info(
        "Tool invoked: opentargets_get_associations(target_id='%s', disease_id='%s', size=%s)",
        target_id,
        disease_id,
        size,
    )
    try:
        result = await opentargets_client.get_associations(
            target_id=target_id, disease_id=disease_id, size=size
        )
        result = validate_list_response(
            result,
            OpenTargetsAssociation,
            list_key="data",
            api_name="OpenTargets",
        )
        return result
    except Exception as e:  # pragma: no cover - defensive
        logger.error("Tool failed: opentargets_get_associations() - %s", e, exc_info=True)
        return {"api_source": "OpenTargets", "data": None, "error": str(e)}


@medmcps_tool(name="opentargets_get_evidence", servers=[opentargets_mcp, unified_mcp])
async def opentargets_get_evidence(
    target_id: str,
    disease_id: str,
    size: int = 25,
) -> dict:
    """Get evidence linking a target and disease."""
    logger.info(
        "Tool invoked: opentargets_get_evidence(target_id='%s', disease_id='%s', size=%s)",
        target_id,
        disease_id,
        size,
    )
    try:
        result = await opentargets_client.get_evidence(
            target_id=target_id, disease_id=disease_id, size=size
        )
        result = validate_list_response(
            result,
            OpenTargetsAssociation,
            list_key="data",
            api_name="OpenTargets",
        )
        return result
    except Exception as e:  # pragma: no cover - defensive
        logger.error("Tool failed: opentargets_get_evidence() - %s", e, exc_info=True)
        return {"api_source": "OpenTargets", "data": None, "error": str(e)}
