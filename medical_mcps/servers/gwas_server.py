#!/usr/bin/env python3
"""
GWAS Catalog API MCP Server
Exposes GWAS Catalog API tools via MCP at /tools/gwas/mcp
"""

import logging

from mcp.server.fastmcp import FastMCP

from ..api_clients.gwas_client import GWASClient
from ..med_mcp_server import tool as medmcps_tool
from ..med_mcp_server import unified_mcp

logger = logging.getLogger(__name__)

# Initialize API client
gwas_client = GWASClient()

# Create FastMCP server for GWAS Catalog
gwas_mcp = FastMCP(
    "gwas-api-server",
    stateless_http=True,
    json_response=True,
)


@medmcps_tool(name="gwas_get_association", servers=[gwas_mcp, unified_mcp])
async def get_association(association_id: str) -> dict:
    """Get association information from GWAS Catalog by ID.

    Args:
        association_id: GWAS association ID
    """
    try:
        return await gwas_client.get_association(association_id)
    except Exception as e:
        logger.error(
            f"Error calling GWAS Catalog API (get_association): {e}", exc_info=True
        )
        return f"Error calling GWAS Catalog API: {str(e)}"


@medmcps_tool(name="gwas_search_associations", servers=[gwas_mcp, unified_mcp])
async def search_associations(
    query: str = None,
    variant_id: str = None,
    study_id: str = None,
    trait: str = None,
    size: int = 20,
    page: int = 0,
) -> dict:
    """Search for associations in GWAS Catalog.

    Args:
        query: General search query. Optional
        variant_id: Variant ID (e.g., 'rs3093017'). Optional
        study_id: Study ID (e.g., 'GCST90132222'). Optional
        trait: Trait name. Optional
        size: Number of results per page. Default: 20
        page: Page number (0-indexed). Default: 0
    """
    try:
        return await gwas_client.search_associations(
            query, variant_id, study_id, trait, size, page
        )
    except Exception as e:
        logger.error(
            f"Error calling GWAS Catalog API (search_associations): {e}", exc_info=True
        )
        return f"Error calling GWAS Catalog API: {str(e)}"


@medmcps_tool(name="gwas_get_variant", servers=[gwas_mcp, unified_mcp])
async def get_variant(variant_id: str) -> dict:
    """Get single nucleotide polymorphism (SNP) information from GWAS Catalog by rsId.

    IMPORTANT: Use rsId format like 'rs3093017' or 'rs4654925'. This queries the
    /singleNucleotidePolymorphisms endpoint, not a general variant search.

    Args:
        variant_id: SNP rsId (e.g., 'rs3093017', 'rs4654925')

    Returns:
        JSON with SNP details including chromosomal location, functional class, and genomic contexts
    """
    try:
        return await gwas_client.get_variant(variant_id)
    except Exception as e:
        logger.error(
            f"Error calling GWAS Catalog API (get_variant): {e}", exc_info=True
        )
        return f"Error calling GWAS Catalog API: {str(e)}"


@medmcps_tool(name="gwas_search_variants", servers=[gwas_mcp, unified_mcp])
async def search_variants(query: str = None, size: int = 20, page: int = 0) -> dict:
    """Search for SNPs/variants in GWAS Catalog by rsId.

    IMPORTANT: The 'query' parameter should be an rsId (e.g., 'rs3093017'). This searches
    the /singleNucleotidePolymorphisms endpoint. For broader variant searches across
    associations, use search_associations with variant_id parameter instead.

    Args:
        query: SNP rsId to search for (e.g., 'rs3093017'). Optional
        size: Number of results per page. Default: 20
        page: Page number (0-indexed). Default: 0

    Returns:
        JSON with list of matching SNPs and pagination info
    """
    try:
        return await gwas_client.search_variants(query, size, page)
    except Exception as e:
        logger.error(
            f"Error calling GWAS Catalog API (search_variants): {e}", exc_info=True
        )
        return f"Error calling GWAS Catalog API: {str(e)}"


@medmcps_tool(name="gwas_get_study", servers=[gwas_mcp, unified_mcp])
async def get_study(study_id: str) -> dict:
    """Get study information from GWAS Catalog by ID.

    Args:
        study_id: Study ID (e.g., 'GCST90132222')
    """
    try:
        return await gwas_client.get_study(study_id)
    except Exception as e:
        logger.error(f"Error calling GWAS Catalog API (get_study): {e}", exc_info=True)
        return f"Error calling GWAS Catalog API: {str(e)}"


@medmcps_tool(name="gwas_search_studies", servers=[gwas_mcp, unified_mcp])
async def search_studies(
    query: str = None, trait: str = None, size: int = 20, page: int = 0
) -> dict:
    """Search for studies in GWAS Catalog.

    Args:
        query: Search query. Optional
        trait: Trait name. Optional
        size: Number of results per page. Default: 20
        page: Page number (0-indexed). Default: 0
    """
    try:
        return await gwas_client.search_studies(query, trait, size, page)
    except Exception as e:
        logger.error(
            f"Error calling GWAS Catalog API (search_studies): {e}", exc_info=True
        )
        return f"Error calling GWAS Catalog API: {str(e)}"


@medmcps_tool(name="gwas_get_trait", servers=[gwas_mcp, unified_mcp])
async def get_trait(trait_id: str) -> dict:
    """Get trait information from GWAS Catalog by ID.

    Args:
        trait_id: EFO trait ID
    """
    try:
        return await gwas_client.get_trait(trait_id)
    except Exception as e:
        logger.error(f"Error calling GWAS Catalog API (get_trait): {e}", exc_info=True)
        return f"Error calling GWAS Catalog API: {str(e)}"


@medmcps_tool(name="gwas_search_traits", servers=[gwas_mcp, unified_mcp])
async def search_traits(query: str = None, size: int = 20, page: int = 0) -> dict:
    """Search for traits in GWAS Catalog.

    Args:
        query: Search query (trait name). Optional
        size: Number of results per page. Default: 20
        page: Page number (0-indexed). Default: 0
    """
    try:
        return await gwas_client.search_traits(query, size, page)
    except Exception as e:
        logger.error(
            f"Error calling GWAS Catalog API (search_traits): {e}", exc_info=True
        )
        return f"Error calling GWAS Catalog API: {str(e)}"
