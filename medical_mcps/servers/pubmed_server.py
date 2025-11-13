#!/usr/bin/env python3
"""
PubMed/PubTator3 API MCP Server
Exposes PubMed article search and retrieval tools via MCP at /tools/pubmed/mcp
"""

import logging

from mcp.server.fastmcp import FastMCP
from ..med_mcp_server import unified_mcp, tool as medmcps_tool

from ..api_clients.pubmed_client import PubMedClient

logger = logging.getLogger(__name__)

# Initialize API client
pubmed_client = PubMedClient()

# Create FastMCP server for PubMed
pubmed_mcp = FastMCP(
    "pubmed-api-server",
    stateless_http=True,
    json_response=True,
)


@medmcps_tool(name="pubmed_search_articles", servers=[pubmed_mcp, unified_mcp])
async def search_articles(
    genes: list[str] | None = None,
    diseases: list[str] | None = None,
    chemicals: list[str] | None = None,
    keywords: list[str] | None = None,
    variants: list[str] | None = None,
    limit: int = 50,
    page: int = 1,
) -> dict:
    """Search biomedical articles from PubMed/PubTator3.

    Args:
        genes: List of gene names (e.g., ['BRAF', 'TP53'])
        diseases: List of disease names (e.g., ['multiple sclerosis', 'melanoma'])
        chemicals: List of chemical/drug names (e.g., ['ocrelizumab'])
        keywords: List of keywords for filtering results. Supports OR logic with pipe separator (e.g., ['R173|Arg173|p.R173'])
        variants: List of variant names (e.g., ['V600E'])
        limit: Maximum number of results per page (default: 50)
        page: Page number (1-based, default: 1)

    Returns:
        JSON with list of articles including PMID, title, journal, authors, date, DOI, abstract
    """
    logger.info(
        f"Tool invoked: search_articles(genes={genes}, diseases={diseases}, chemicals={chemicals}, keywords={keywords}, variants={variants}, limit={limit}, page={page})"
    )
    try:
        result = await pubmed_client.search_articles(
            genes=genes,
            diseases=diseases,
            chemicals=chemicals,
            keywords=keywords,
            variants=variants,
            limit=limit,
            page=page,
        )
        logger.info("Tool succeeded: search_articles()")
        return result
    except Exception as e:
        logger.error(f"Tool failed: search_articles() - {e}", exc_info=True)
        return {
            "api_source": "PubMed",
            "data": [],
            "error": f"Error calling PubMed API: {str(e)}",
        }


@medmcps_tool(name="pubmed_get_article", servers=[pubmed_mcp, unified_mcp])
async def get_article(pmid_or_doi: str, full: bool = False) -> dict:
    """Get detailed article information by PMID or DOI.

    Args:
        pmid_or_doi: PubMed ID (numeric, e.g., '34397683') or DOI (e.g., '10.1101/2024.01.20.23288905')
        full: Whether to fetch full text (default: False, returns abstract only)

    Returns:
        JSON with article details including title, abstract, authors, journal, date, and optionally full text
    """
    logger.info(f"Tool invoked: get_article(pmid_or_doi='{pmid_or_doi}', full={full})")
    try:
        result = await pubmed_client.get_article(pmid_or_doi, full=full)
        logger.info(f"Tool succeeded: get_article(pmid_or_doi='{pmid_or_doi}')")
        return result
    except Exception as e:
        logger.error(
            f"Tool failed: get_article(pmid_or_doi='{pmid_or_doi}') - {e}",
            exc_info=True,
        )
        return {
            "api_source": "PubMed",
            "data": None,
            "error": f"Error calling PubMed API: {str(e)}",
        }


@medmcps_tool(name="pubmed_search_preprints", servers=[pubmed_mcp, unified_mcp])
async def search_preprints(query: str, limit: int = 25) -> dict:
    """Search preprint articles from bioRxiv/medRxiv via Europe PMC.

    Args:
        query: Search query (e.g., 'multiple sclerosis CD20')
        limit: Maximum number of results (default: 25, max: 1000)

    Returns:
        JSON with list of preprints including DOI, title, authors, journal, date, abstract
    """
    logger.info(f"Tool invoked: search_preprints(query='{query}', limit={limit})")
    try:
        result = await pubmed_client.search_preprints(query, limit=limit)
        logger.info(f"Tool succeeded: search_preprints(query='{query}')")
        return result
    except Exception as e:
        logger.error(
            f"Tool failed: search_preprints(query='{query}') - {e}",
            exc_info=True,
        )
        return {
            "api_source": "PubMed",
            "data": [],
            "error": f"Error calling PubMed API: {str(e)}",
        }
