#!/usr/bin/env python3
"""
Pathway Commons API MCP Server
Exposes Pathway Commons API tools via MCP at /tools/pathwaycommons/mcp
"""

import logging

from mcp.server.fastmcp import FastMCP
from ..med_mcp_server import unified_mcp, tool as medmcps_tool

from ..api_clients.pathwaycommons_client import PathwayCommonsClient

logger = logging.getLogger(__name__)

# Initialize API client
pathwaycommons_client = PathwayCommonsClient()

# Create FastMCP server for Pathway Commons
pathwaycommons_mcp = FastMCP(
    "pathwaycommons-api-server",
    stateless_http=True,
    json_response=True,
)


@medmcps_tool(name="pathwaycommons_search", servers=[pathwaycommons_mcp, unified_mcp])
async def search_pathwaycommons(
    q: str,
    type: str = "Pathway",
    format: str = "json",
    page: int = 0,
    datasource: str = None,
) -> dict:
    """Search Pathway Commons for pathways, proteins, or other biological entities.

    WARNING: This tool may take up to 2-3 minutes to respond. The upstream Pathway Commons API
    is very slow and may timeout on complex queries. Please be patient when using this tool.

    Args:
        q: Search query
        type: Entity type ('Pathway', 'Protein', 'Gene', etc.). Default: 'Pathway'
              NOTE: For gene symbols, use type='Protein' (not 'Gene'). The 'Gene' type rarely returns results.
        format: Response format ('json', 'xml', 'biopax'). Default: 'json'
        page: Page number. Default: 0
        datasource: Data source filter (e.g., 'Reactome', 'KEGG'). Optional
    """
    logger.info(
        f"Tool invoked: search_pathwaycommons(q='{q}', type='{type}', format='{format}', page={page}, datasource='{datasource}')"
    )

    # Warn if searching for gene with type='Gene'
    if type == "Gene":
        logger.warning(
            f"search_pathwaycommons() called with type='Gene' for query '{q}'. "
            "Consider using type='Protein' instead for better results with gene symbols."
        )

    try:
        result = await pathwaycommons_client.search(q, type, format, page, datasource)
        logger.info(f"Tool succeeded: search_pathwaycommons(q='{q}', type='{type}')")
        return result
    except Exception as e:
        logger.error(
            f"Tool failed: search_pathwaycommons(q='{q}', type='{type}') - {e}", exc_info=True
        )
        return f"Error calling Pathway Commons API: {str(e)}"


@medmcps_tool(name="pathwaycommons_get_pathway_by_uri", servers=[pathwaycommons_mcp, unified_mcp])
async def get_pathway_by_uri(uri: str, format: str = "json") -> dict | str:
    """Get pathway information from Pathway Commons by URI.

    Args:
        uri: Pathway URI (e.g., 'http://identifiers.org/reactome/R-HSA-1640170')
        format: Response format ('json', 'xml', 'biopax'). Default: 'json'
    """
    logger.info(f"Tool invoked: get_pathway_by_uri(uri='{uri}', format='{format}')")
    try:
        result = await pathwaycommons_client.get_pathway(uri, format)
        logger.info(f"Tool succeeded: get_pathway_by_uri(uri='{uri}')")
        return result
    except Exception as e:
        logger.error(
            f"Tool failed: get_pathway_by_uri(uri='{uri}') - {e}", exc_info=True
        )
        return f"Error calling Pathway Commons API: {str(e)}"


@medmcps_tool(name="pathwaycommons_top_pathways", servers=[pathwaycommons_mcp, unified_mcp])
async def top_pathways(
    gene: str = None, datasource: str = None, limit: int = 10
) -> dict:
    """Get top-level pathways from Pathway Commons using v2 POST API.

    WARNING: This tool may take up to 2-3 minutes to respond. The upstream Pathway Commons API
    is very slow and may timeout. Please be patient when using this tool.

    Finds root/parent Pathway objects that are neither controlled nor pathwayComponent
    of another biological process. Trivial pathways are excluded.

    Args:
        gene: Gene symbol or ID to search for in pathways (used as Lucene query). 
              If not provided, returns all top pathways. Optional
        datasource: Data source filter (e.g., 'reactome', 'kegg'). Optional
        limit: Maximum number of results. Default: 10

    Returns:
        JSON with top pathways matching the criteria
    """
    logger.info(
        f"Tool invoked: top_pathways(gene='{gene}', datasource='{datasource}', limit={limit})"
    )
    try:
        result = await pathwaycommons_client.top_pathways(gene, datasource, limit)
        logger.info(
            f"Tool succeeded: top_pathways(gene='{gene}', datasource='{datasource}')"
        )
        return result
    except Exception as e:
        logger.error(f"Tool failed: top_pathways(gene='{gene}') - {e}", exc_info=True)
        return f"Error calling Pathway Commons API: {str(e)}"


@medmcps_tool(name="pathwaycommons_graph", servers=[pathwaycommons_mcp, unified_mcp])
async def graph(
    source: str,
    target: str = None,
    kind: str = "neighborhood",
    limit: int = 1,
    format: str = "json",
) -> dict | str:
    """Get pathway graph/network from Pathway Commons using v2 POST API.

    IMPORTANT: Uses v2 API which requires POST requests. The 'kind' parameter determines
    which endpoint is used: 'neighborhood', 'pathsbetween', 'pathsfromto', or 'commonstream'.

    Args:
        source: Source entity in CURIE format (e.g., 'HGNC:6008', 'UniProt:P01589'). Plain gene symbols NOT supported.
        target: Target entity in CURIE format (optional, only used for 'pathsfromto' kind)
        kind: Graph kind - 'neighborhood' (default), 'pathsbetween', 'pathsfromto', 'commonstream'
        limit: Path length limit. Default: 1
        format: Response format - 'json' (default), 'sif', 'txt', 'biopax', 'jsonld'

    Returns:
        Graph data in requested format showing network relationships
    """
    logger.info(
        f"Tool invoked: graph(source='{source}', target='{target}', kind='{kind}', limit={limit})"
    )

    # Validate CURIE format for source
    if ":" not in source or source.startswith("http"):
        return (
            f"Error: Invalid source identifier '{source}'. "
            "The 'source' parameter must be in CURIE format (e.g., 'HGNC:6008', 'UniProt:P01589'). "
            "Plain gene symbols like 'IL2RA' or 'BRCA1' are not supported. "
            "Use UniProt map_ids tool to convert gene names to UniProt IDs first, "
            "or search for the gene in Pathway Commons to get its CURIE identifier."
        )

    # Validate CURIE format for target if provided
    if target and (":" not in target or target.startswith("http")):
        return (
            f"Error: Invalid target identifier '{target}'. "
            "The 'target' parameter must be in CURIE format (e.g., 'HGNC:6008', 'UniProt:P01589'). "
            "Plain gene symbols are not supported."
        )

    try:
        result = await pathwaycommons_client.graph(source, target, kind, limit, format)
        logger.info(f"Tool succeeded: graph(source='{source}', kind='{kind}')")
        return result
    except Exception as e:
        logger.error(f"Tool failed: graph(source='{source}') - {e}", exc_info=True)
        return f"Error calling Pathway Commons API: {str(e)}"


@medmcps_tool(name="pathwaycommons_traverse", servers=[pathwaycommons_mcp, unified_mcp])
async def traverse(uri: str, path: str, format: str = "json") -> dict | str:
    """Traverse pathway data in Pathway Commons using v2 POST API.

    IMPORTANT: Uses v2 API which requires POST requests. Access properties of BioPAX elements
    using graph path expressions (xpath-like syntax).

    Args:
        uri: Pathway or entity URI (e.g., 'http://identifiers.org/reactome/R-HSA-1640170')
        path: Traversal path expression (e.g., 'Pathway/pathwayComponent:Interaction/participant*/displayName')
              Use '*' for transitive traversal, ':filterClass' to filter by class
        format: Response format ('json', 'xml'). Default: 'json'

    Returns:
        Traversal results with requested property values
    """
    logger.info(
        f"Tool invoked: traverse(uri='{uri}', path='{path}', format='{format}')"
    )
    try:
        result = await pathwaycommons_client.traverse(uri, path, format)
        logger.info(f"Tool succeeded: traverse(uri='{uri}', path='{path}')")
        return result
    except Exception as e:
        logger.error(
            f"Tool failed: traverse(uri='{uri}', path='{path}') - {e}", exc_info=True
        )
        return f"Error calling Pathway Commons API: {str(e)}"
