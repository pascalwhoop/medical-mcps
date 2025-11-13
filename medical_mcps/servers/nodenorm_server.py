#!/usr/bin/env python3
"""
Node Normalization API MCP Server
Exposes Node Normalization API tools via MCP at /tools/nodenorm/mcp

Node Normalization is a utility service that normalizes CURIEs (Compact URIs)
across biological databases, returning equivalent identifiers and semantic types.
"""

import logging

from mcp.server.fastmcp import FastMCP
from ..med_mcp_server import unified_mcp, tool as medmcps_tool

from ..api_clients.nodenorm_client import NodeNormClient

logger = logging.getLogger(__name__)

# Initialize API client
nodenorm_client = NodeNormClient()

# Create FastMCP server for Node Normalization
nodenorm_mcp = FastMCP(
    "nodenorm-api-server",
    stateless_http=True,
    json_response=True,
)


@medmcps_tool(name="nodenorm_get_semantic_types", servers=[nodenorm_mcp, unified_mcp])
async def get_semantic_types() -> str:
    """Get all BioLink semantic types for which normalization has been attempted.

    This endpoint returns the semantic types (categories) that Node Normalization
    can handle. Use this to determine which entity types can be normalized.

    Returns a dictionary mapping semantic types to their metadata.
    """
    try:
        result = await nodenorm_client.get_semantic_types()
        return result
    except Exception as e:
        logger.error(
            f"Error calling Node Normalization API (get_semantic_types): {e}",
            exc_info=True,
        )
        return f"Error calling Node Normalization API: {str(e)}"


@medmcps_tool(name="nodenorm_get_curie_prefixes", servers=[nodenorm_mcp, unified_mcp])
async def get_curie_prefixes() -> str:
    """Get all CURIE prefixes available in the normalization database.

    This endpoint returns the list of supported CURIE prefixes (e.g., DRUGBANK,
    MONDO, NCIT, CHEBI) and shows how many times each prefix is used for each
    semantic type. Use this to determine the correct prefix format when constructing
    CURIEs for normalization.

    Example prefixes:
    - DRUGBANK:DB05266 (DrugBank drug)
    - MONDO:0001134 (Monarch Disease Ontology disease)
    - NCIT:C34373 (NCI Thesaurus concept)
    - CHEBI:15365 (Chemical Entities of Biological Interest)
    """
    try:
        result = await nodenorm_client.get_curie_prefixes()
        return result
    except Exception as e:
        logger.error(
            f"Error calling Node Normalization API (get_curie_prefixes): {e}",
            exc_info=True,
        )
        return f"Error calling Node Normalization API: {str(e)}"


@medmcps_tool(name="nodenorm_get_normalized_nodes", servers=[nodenorm_mcp, unified_mcp])
async def get_normalized_nodes(
    curies: str,
    conflate: bool = True,
    drug_chemical_conflate: bool = False,
    description: bool = False,
    individual_types: bool = False,
    include_taxa: bool = True,
) -> str:
    """Get normalized identifiers and semantic types for one or more CURIEs.

    This is the core normalization function. Given a CURIE from any source database,
    it returns:
    1. The preferred CURIE for this entity
    2. All equivalent identifiers across databases
    3. Semantic types from the BioLink Model

    Args:
        curies: Comma-separated list of CURIEs to normalize (e.g., 'DRUGBANK:DB05266,MONDO:0001134')
                Each CURIE must use the format PREFIX:ID where PREFIX comes from get_curie_prefixes()
        conflate: Whether to apply gene/protein conflation (default: True)
        drug_chemical_conflate: Whether to apply drug/chemical conflation (default: False)
        description: Whether to return CURIE descriptions when possible (default: False)
        individual_types: Whether to return individual types for equivalent identifiers (default: False)
        include_taxa: Whether to return taxa for equivalent identifiers (default: True)

    Example:
        Input: 'DRUGBANK:DB05266'
        Returns normalized node with equivalent identifiers and semantic types
    """
    try:
        # Parse comma-separated CURIEs
        curie_list = [c.strip() for c in curies.split(",") if c.strip()]
        if not curie_list:
            return "Error: At least one CURIE must be provided"

        result = await nodenorm_client.get_normalized_nodes(
            curies=curie_list,
            conflate=conflate,
            drug_chemical_conflate=drug_chemical_conflate,
            description=description,
            individual_types=individual_types,
            include_taxa=include_taxa,
        )
        return result
    except Exception as e:
        logger.error(
            f"Error calling Node Normalization API (get_normalized_nodes): {e}",
            exc_info=True,
        )
        return f"Error calling Node Normalization API: {str(e)}"


@medmcps_tool(name="nodenorm_get_allowed_conflations", servers=[nodenorm_mcp, unified_mcp])
async def get_allowed_conflations() -> str:
    """Get the available conflation types that can be applied during normalization.

    Conflations merge equivalent entities across different representations:
    - Gene/Protein conflation: Merges gene and protein identifiers
    - Drug/Chemical conflation: Merges drug and chemical entity identifiers

    Returns a list of available conflation types that can be used in normalization.
    """
    try:
        result = await nodenorm_client.get_allowed_conflations()
        return result
    except Exception as e:
        logger.error(
            f"Error calling Node Normalization API (get_allowed_conflations): {e}",
            exc_info=True,
        )
        return f"Error calling Node Normalization API: {str(e)}"
