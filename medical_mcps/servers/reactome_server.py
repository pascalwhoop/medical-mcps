#!/usr/bin/env python3
"""
Reactome API MCP Server
Exposes Reactome API tools via MCP at /tools/reactome/mcp
"""

import logging

from mcp.server.fastmcp import FastMCP
from ..med_mcp_server import unified_mcp, tool as medmcps_tool

from ..api_clients.reactome_client import ReactomeClient

logger = logging.getLogger(__name__)

# Initialize API client
reactome_client = ReactomeClient()

# Create FastMCP server for Reactome
reactome_mcp = FastMCP(
    "reactome-api-server",
    stateless_http=True,
    json_response=True,
)


@medmcps_tool(name="reactome_get_pathway", servers=[reactome_mcp, unified_mcp])
async def get_pathway(pathway_id: str) -> dict:
    """Get pathway information from Reactome API. Returns detailed pathway data including name, species, and related entities.

    IMPORTANT: Use Reactome pathway IDs that start with 'R-' (e.g., 'R-HSA-1640170').
    Do NOT use KEGG pathway IDs (e.g., 'hsa04010') - those are for KEGG API only.

    Pathway ID format: R-<ORG>-<NUMBER>
    - R-HSA-1640170 (Human)
    - R-MMU-1640170 (Mouse)
    - R-RNO-1640170 (Rat)

    Args:
        pathway_id: Reactome pathway stable identifier (e.g., 'R-HSA-1640170')

    Returns:
        JSON with pathway details including name, species, GO terms, sub-pathways, and related entities
    """
    logger.info(f"Tool invoked: get_pathway(pathway_id='{pathway_id}')")
    try:
        result = await reactome_client.get_pathway(pathway_id)
        logger.info(f"Tool succeeded: get_pathway(pathway_id='{pathway_id}')")
        return result
    except Exception as e:
        # Check if this is a validation error (user error) vs server error
        is_validation_error = (
            "Invalid pathway ID format" in str(e) or "not found" in str(e).lower()
        )
        if is_validation_error:
            logger.warning(
                f"Tool validation error: get_pathway(pathway_id='{pathway_id}') - {e}"
            )
        else:
            logger.error(
                f"Tool failed: get_pathway(pathway_id='{pathway_id}') - {e}",
                exc_info=True,
            )
        return f"Error calling Reactome API: {str(e)}"


@medmcps_tool(name="reactome_query_pathways", servers=[reactome_mcp, unified_mcp])
async def query_pathways(query: str, species: str = "Homo sapiens") -> dict:
    """Query pathways from Reactome API by keyword or gene/protein name. Returns matching pathways.

    IMPORTANT: This searches Reactome's full-text index. Use gene symbols, protein names,
    or pathway keywords. Results are filtered to only return Pathway objects.

    Args:
        query: Search query (pathway name, gene symbol like 'TAGAP', or protein name)
        species: Species filter (e.g., 'Homo sapiens', '9606' for human, 'Mus musculus' for mouse).
                 Default: 'Homo sapiens'. Can use species name or NCBI taxon ID.

    Returns:
        JSON with list of matching pathways, each including stId, name, species, and summary
    """
    logger.info(f"Tool invoked: query_pathways(query='{query}', species='{species}')")
    try:
        result = await reactome_client.query_pathways(query, species)
        logger.info(
            f"Tool succeeded: query_pathways(query='{query}', species='{species}')"
        )
        return result
    except Exception as e:
        logger.error(
            f"Tool failed: query_pathways(query='{query}', species='{species}') - {e}",
            exc_info=True,
        )
        return f"Error calling Reactome API: {str(e)}"


@medmcps_tool(name="reactome_get_pathway_participants", servers=[reactome_mcp, unified_mcp])
async def get_pathway_participants(pathway_id: str) -> dict | list:
    """Get all participants (genes, proteins, small molecules) in a Reactome pathway.

    IMPORTANT: Not all pathways have a direct participants endpoint. If unavailable,
    the tool returns pathway information instead with a note. Use query_pathways()
    with a gene/protein name to find pathways containing specific participants.

    Args:
        pathway_id: Reactome pathway stable identifier (e.g., 'R-HSA-1640170')

    Returns:
        JSON with list of participants (genes, proteins, small molecules) or pathway info if endpoint unavailable
    """
    logger.info(f"Tool invoked: get_pathway_participants(pathway_id='{pathway_id}')")
    try:
        result = await reactome_client.get_pathway_participants(pathway_id)
        logger.info(
            f"Tool succeeded: get_pathway_participants(pathway_id='{pathway_id}')"
        )
        return result
    except Exception as e:
        is_validation_error = (
            "Invalid pathway ID format" in str(e) or "not found" in str(e).lower()
        )
        if is_validation_error:
            logger.warning(
                f"Tool validation error: get_pathway_participants(pathway_id='{pathway_id}') - {e}"
            )
        else:
            logger.error(
                f"Tool failed: get_pathway_participants(pathway_id='{pathway_id}') - {e}",
                exc_info=True,
            )
        return f"Error calling Reactome API: {str(e)}"


@medmcps_tool(name="reactome_get_disease_pathways", servers=[reactome_mcp, unified_mcp])
async def get_disease_pathways(disease_name: str) -> dict | list:
    """Get pathways associated with a disease from Reactome API.

    IMPORTANT: This searches for disease entities in Reactome and retrieves their associated pathways.
    Not all diseases have pathway associations in Reactome. If none found, returns empty list with
    suggestion to use query_pathways() instead.

    Args:
        disease_name: Disease name (e.g., 'multiple sclerosis', 'Alzheimer disease', 'diabetes')

    Returns:
        JSON with list of pathways associated with the disease, or empty list if none found
    """
    logger.info(f"Tool invoked: get_disease_pathways(disease_name='{disease_name}')")
    try:
        result = await reactome_client.get_disease_pathways(disease_name)
        logger.info(
            f"Tool succeeded: get_disease_pathways(disease_name='{disease_name}')"
        )
        return result
    except Exception as e:
        logger.error(
            f"Tool failed: get_disease_pathways(disease_name='{disease_name}') - {e}",
            exc_info=True,
        )
        return f"Error calling Reactome API: {str(e)}"
