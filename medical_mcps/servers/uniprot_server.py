#!/usr/bin/env python3
"""
UniProt API MCP Server
Exposes UniProt API tools via MCP at /tools/uniprot/mcp
"""

import logging

from mcp.server.fastmcp import FastMCP

from ..api_clients.uniprot_client import UniProtClient

logger = logging.getLogger(__name__)

# Initialize API client
uniprot_client = UniProtClient()

# Create FastMCP server for UniProt
uniprot_mcp = FastMCP(
    "uniprot-api-server",
    stateless_http=True,
    json_response=True,
)


@uniprot_mcp.tool(name="uniprot_get_protein")
async def get_protein(accession: str, format: str = "json") -> dict | str:
    """Get protein information from UniProt by accession.

    Args:
        accession: UniProt accession (e.g., 'P00520')
        format: Response format ('json', 'fasta', 'xml'). Default: 'json'
    """
    logger.info(
        f"Tool invoked: get_protein(accession='{accession}', format='{format}')"
    )
    try:
        result = await uniprot_client.get_protein(accession, format)
        logger.info(f"Tool succeeded: get_protein(accession='{accession}')")
        return result
    except Exception as e:
        logger.error(
            f"Tool failed: get_protein(accession='{accession}') - {e}", exc_info=True
        )
        return f"Error calling UniProt API: {str(e)}"


@uniprot_mcp.tool(name="uniprot_search_proteins")
async def search_proteins(
    query: str, format: str = "json", limit: int = 25, offset: int = 0
) -> dict | str:
    """Search proteins in UniProtKB.

    Args:
        query: Search query (e.g., 'gene:BRCA1 AND organism_id:9606')
        format: Response format ('json', 'tsv', 'fasta'). Default: 'json'
        limit: Maximum number of results. Default: 25
        offset: Offset for pagination. Default: 0
    """
    logger.info(
        f"Tool invoked: search_proteins(query='{query}', format='{format}', limit={limit}, offset={offset})"
    )
    try:
        result = await uniprot_client.search_proteins(query, format, limit, offset)
        logger.info(f"Tool succeeded: search_proteins(query='{query}')")
        return result
    except Exception as e:
        logger.error(
            f"Tool failed: search_proteins(query='{query}') - {e}", exc_info=True
        )
        return f"Error calling UniProt API: {str(e)}"


@uniprot_mcp.tool(name="uniprot_get_protein_sequence")
async def get_protein_sequence(accession: str) -> str:
    """Get protein sequence in FASTA format.

    Args:
        accession: UniProt accession
    """
    logger.info(f"Tool invoked: get_protein_sequence(accession='{accession}')")
    try:
        result = await uniprot_client.get_protein_sequence(accession)
        logger.info(f"Tool succeeded: get_protein_sequence(accession='{accession}')")
        return result
    except Exception as e:
        logger.error(
            f"Tool failed: get_protein_sequence(accession='{accession}') - {e}",
            exc_info=True,
        )
        return f"Error calling UniProt API: {str(e)}"


@uniprot_mcp.tool(name="uniprot_get_disease_associations")
async def get_disease_associations(accession: str) -> dict:
    """Get disease associations for a protein.

    Args:
        accession: UniProt accession
    """
    logger.info(f"Tool invoked: get_disease_associations(accession='{accession}')")
    try:
        result = await uniprot_client.get_disease_associations(accession)
        logger.info(
            f"Tool succeeded: get_disease_associations(accession='{accession}')"
        )
        return result
    except Exception as e:
        logger.error(
            f"Tool failed: get_disease_associations(accession='{accession}') - {e}",
            exc_info=True,
        )
        return f"Error calling UniProt API: {str(e)}"


@uniprot_mcp.tool(name="uniprot_map_ids")
async def map_ids(from_db: str, to_db: str, ids: str) -> dict | str:
    """Map identifiers between databases using UniProt ID mapping.

    IMPORTANT: This is an asynchronous job that may take 1-30 seconds. The tool automatically
    polls for results and returns them when ready.

    Common database names:
    - From: 'Gene_Name', 'UniProtKB_AC-ID', 'P_ENTREZGENEID', 'Ensembl', 'RefSeq_Protein'
    - To: 'UniProtKB', 'UniProtKB-Swiss-Prot', 'Ensembl', 'Ensembl_Protein', 'GeneID'

    Use the search() method first if you're unsure of valid database names.

    Args:
        from_db: Source database (e.g., 'Gene_Name', 'UniProtKB_AC-ID')
        to_db: Target database (e.g., 'UniProtKB', 'Ensembl')
        ids: Comma-separated list of identifiers (e.g., 'TAGAP,BRCA1,TP53' or 'P21802,P12345')

    Returns:
        JSON with mapping results including jobId, mapped results, and any failed IDs
    """
    logger.info(
        f"Tool invoked: map_ids(from_db='{from_db}', to_db='{to_db}', ids='{ids}')"
    )
    try:
        id_list = [id.strip() for id in ids.split(",")]
        result = await uniprot_client.map_ids(from_db, to_db, id_list)
        logger.info(f"Tool succeeded: map_ids(from_db='{from_db}', to_db='{to_db}')")
        return result
    except Exception as e:
        logger.error(
            f"Tool failed: map_ids(from_db='{from_db}', to_db='{to_db}') - {e}",
            exc_info=True,
        )
        return f"Error calling UniProt API: {str(e)}"
