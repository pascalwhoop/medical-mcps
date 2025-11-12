#!/usr/bin/env python3
"""
OMIM API MCP Server
Exposes OMIM API tools via MCP at /tools/omim/mcp
API key MUST be provided by the MCP client with each request
"""

import logging

from mcp.server.fastmcp import FastMCP

from ..api_clients.omim_client import OMIMClient

logger = logging.getLogger(__name__)

# Create FastMCP server for OMIM
omim_mcp = FastMCP(
    "omim-api-server",
    stateless_http=True,
    json_response=True,
)


@omim_mcp.tool(name="omim_get_entry")
async def get_entry(mim_number: str, api_key: str, include: str = "text") -> dict:
    """Get entry information from OMIM by MIM number.
    
    Args:
        mim_number: MIM number (e.g., '104300')
        api_key: OMIM API key (REQUIRED - get from https://omim.org/api)
        include: Fields to include ('text', 'allelicVariantList', 'geneMap', etc.). Default: 'text'
    """
    if not api_key:
        return "Error: OMIM API key is required. Get your API key from https://omim.org/api"
    
    try:
        client = OMIMClient(api_key=api_key)
        return await client.get_entry(mim_number, include)
    except Exception as e:
        logger.error(f"Error calling OMIM API (get_entry): {e}", exc_info=True)
        return f"Error calling OMIM API: {str(e)}"


@omim_mcp.tool(name="omim_search_entries")
async def search_entries(
    search: str,
    api_key: str,
    include: str = "text",
    limit: int = 20,
    start: int = 0
) -> dict:
    """Search entries in OMIM.
    
    Args:
        search: Search query
        api_key: OMIM API key (REQUIRED - get from https://omim.org/api)
        include: Fields to include. Default: 'text'
        limit: Maximum number of results. Default: 20
        start: Starting index for pagination. Default: 0
    """
    if not api_key:
        return "Error: OMIM API key is required. Get your API key from https://omim.org/api"
    
    try:
        client = OMIMClient(api_key=api_key)
        return await client.search_entries(search, include, limit, start)
    except Exception as e:
        logger.error(f"Error calling OMIM API (search_entries): {e}", exc_info=True)
        return f"Error calling OMIM API: {str(e)}"


@omim_mcp.tool(name="omim_get_gene")
async def get_gene(gene_symbol: str, api_key: str, include: str = "geneMap") -> dict:
    """Get gene information from OMIM by gene symbol.
    
    Args:
        gene_symbol: Gene symbol (e.g., 'BRCA1')
        api_key: OMIM API key (REQUIRED - get from https://omim.org/api)
        include: Fields to include. Default: 'geneMap'
    """
    if not api_key:
        return "Error: OMIM API key is required. Get your API key from https://omim.org/api"
    
    try:
        client = OMIMClient(api_key=api_key)
        return await client.get_gene(gene_symbol, include)
    except Exception as e:
        logger.error(f"Error calling OMIM API (get_gene): {e}", exc_info=True)
        return f"Error calling OMIM API: {str(e)}"


@omim_mcp.tool(name="omim_search_genes")
async def search_genes(
    search: str,
    api_key: str,
    include: str = "geneMap",
    limit: int = 20,
    start: int = 0
) -> dict:
    """Search genes in OMIM.
    
    Args:
        search: Search query
        api_key: OMIM API key (REQUIRED - get from https://omim.org/api)
        include: Fields to include. Default: 'geneMap'
        limit: Maximum number of results. Default: 20
        start: Starting index for pagination. Default: 0
    """
    if not api_key:
        return "Error: OMIM API key is required. Get your API key from https://omim.org/api"
    
    try:
        client = OMIMClient(api_key=api_key)
        return await client.search_genes(search, include, limit, start)
    except Exception as e:
        logger.error(f"Error calling OMIM API (search_genes): {e}", exc_info=True)
        return f"Error calling OMIM API: {str(e)}"


@omim_mcp.tool(name="omim_get_phenotype")
async def get_phenotype(mim_number: str, api_key: str, include: str = "text") -> dict:
    """Get phenotype information from OMIM by MIM number.
    
    Args:
        mim_number: MIM number
        api_key: OMIM API key (REQUIRED - get from https://omim.org/api)
        include: Fields to include. Default: 'text'
    """
    if not api_key:
        return "Error: OMIM API key is required. Get your API key from https://omim.org/api"
    
    try:
        client = OMIMClient(api_key=api_key)
        return await client.get_phenotype(mim_number, include)
    except Exception as e:
        logger.error(f"Error calling OMIM API (get_phenotype): {e}", exc_info=True)
        return f"Error calling OMIM API: {str(e)}"


@omim_mcp.tool(name="omim_search_phenotypes")
async def search_phenotypes(
    search: str,
    api_key: str,
    include: str = "text",
    limit: int = 20,
    start: int = 0
) -> dict:
    """Search phenotypes in OMIM.
    
    Args:
        search: Search query
        api_key: OMIM API key (REQUIRED - get from https://omim.org/api)
        include: Fields to include. Default: 'text'
        limit: Maximum number of results. Default: 20
        start: Starting index for pagination. Default: 0
    """
    if not api_key:
        return "Error: OMIM API key is required. Get your API key from https://omim.org/api"
    
    try:
        client = OMIMClient(api_key=api_key)
        return await client.search_phenotypes(search, include, limit, start)
    except Exception as e:
        logger.error(f"Error calling OMIM API (search_phenotypes): {e}", exc_info=True)
        return f"Error calling OMIM API: {str(e)}"
