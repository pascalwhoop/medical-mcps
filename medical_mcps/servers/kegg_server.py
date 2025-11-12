#!/usr/bin/env python3
"""
KEGG API MCP Server
Exposes KEGG API tools via MCP at /tools/kegg/mcp
"""

import logging

from mcp.server.fastmcp import FastMCP

from ..api_clients.kegg_client import KEGGClient

logger = logging.getLogger(__name__)

# Initialize API client
kegg_client = KEGGClient()

# Create FastMCP server for KEGG
kegg_mcp = FastMCP(
    "kegg-api-server",
    stateless_http=True,
    json_response=True,
)


@kegg_mcp.tool(name="kegg_get_pathway_info")
async def get_pathway_info(pathway_id: str) -> str:
    """Get pathway information from KEGG by pathway ID.

    Args:
        pathway_id: KEGG pathway ID (e.g., 'hsa04010' for human, 'map00010' for reference)
    """
    try:
        return await kegg_client.get_pathway(pathway_id)
    except Exception as e:
        logger.error(f"Error calling KEGG API (get_pathway_info): {e}", exc_info=True)
        return f"Error calling KEGG API: {str(e)}"


@kegg_mcp.tool(name="kegg_list_pathways")
async def list_pathways(organism: str | None = None) -> str:
    """List pathways from KEGG. If organism is provided, lists organism-specific pathways.

    Args:
        organism: KEGG organism code (e.g., 'hsa' for human). Optional - if not provided, lists reference pathways.
    """
    try:
        return await kegg_client.list_pathways(organism)
    except Exception as e:
        logger.error(f"Error calling KEGG API (list_pathways): {e}", exc_info=True)
        return f"Error calling KEGG API: {str(e)}"


@kegg_mcp.tool(name="kegg_find_pathways")
async def find_pathways(query: str) -> str:
    """Find pathways in KEGG matching a query keyword.

    Args:
        query: Search keyword (pathway name or related term)
    """
    try:
        return await kegg_client.find_pathways(query)
    except Exception as e:
        logger.error(f"Error calling KEGG API (find_pathways): {e}", exc_info=True)
        return f"Error calling KEGG API: {str(e)}"


@kegg_mcp.tool(name="kegg_get_gene")
async def get_gene(gene_id: str) -> str:
    """Get gene information from KEGG by gene ID.

    Args:
        gene_id: KEGG gene ID (e.g., 'hsa:10458')
    """
    try:
        return await kegg_client.get_gene(gene_id)
    except Exception as e:
        logger.error(f"Error calling KEGG API (get_gene): {e}", exc_info=True)
        return f"Error calling KEGG API: {str(e)}"


@kegg_mcp.tool(name="kegg_find_genes")
async def find_genes(query: str, organism: str | None = None) -> str:
    """Find genes in KEGG matching a query keyword.

    Args:
        query: Search keyword (gene name, symbol, etc.)
        organism: KEGG organism code (e.g., 'hsa' for human). Optional.
    """
    try:
        return await kegg_client.find_genes(query, organism)
    except Exception as e:
        logger.error(f"Error calling KEGG API (find_genes): {e}", exc_info=True)
        return f"Error calling KEGG API: {str(e)}"


@kegg_mcp.tool(name="kegg_get_disease")
async def get_disease(disease_id: str) -> str:
    """Get disease information from KEGG by disease ID.

    Args:
        disease_id: KEGG disease ID (e.g., 'H00001')
    """
    try:
        return await kegg_client.get_disease(disease_id)
    except Exception as e:
        logger.error(f"Error calling KEGG API (get_disease): {e}", exc_info=True)
        return f"Error calling KEGG API: {str(e)}"


@kegg_mcp.tool(name="kegg_find_diseases")
async def find_diseases(query: str) -> str:
    """Find diseases in KEGG matching a query keyword.

    Args:
        query: Search keyword (disease name or related term)
    """
    try:
        return await kegg_client.find_diseases(query)
    except Exception as e:
        logger.error(f"Error calling KEGG API (find_diseases): {e}", exc_info=True)
        return f"Error calling KEGG API: {str(e)}"


@kegg_mcp.tool(name="kegg_link_pathway_genes")
async def link_pathway_genes(pathway_id: str) -> str:
    """Get genes linked to a KEGG pathway.

    IMPORTANT: Pathway ID format should be organism code + 5 digits (e.g., 'hsa04658')
    or reference pathway 'map00010'. The tool automatically extracts the organism code.

    Args:
        pathway_id: KEGG pathway ID (e.g., 'hsa04658', 'hsa:04658', 'map00010')

    Returns:
        Tab-delimited list of gene IDs linked to the pathway
    """
    try:
        return await kegg_client.link_pathway_genes(pathway_id)
    except Exception as e:
        logger.error(f"Error calling KEGG API (link_pathway_genes): {e}", exc_info=True)
        return f"Error calling KEGG API: {str(e)}"
