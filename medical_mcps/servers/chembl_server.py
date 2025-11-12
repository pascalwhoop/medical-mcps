#!/usr/bin/env python3
"""
ChEMBL API MCP Server
Exposes ChEMBL API tools via MCP at /tools/chembl/mcp
"""

import logging

from mcp.server.fastmcp import FastMCP

from ..api_clients.chembl_client import ChEMBLClient

logger = logging.getLogger(__name__)

# Initialize API client
chembl_client = ChEMBLClient()

# Create FastMCP server for ChEMBL
chembl_mcp = FastMCP(
    "chembl-api-server",
    stateless_http=True,
    json_response=True,
)


@chembl_mcp.tool(name="chembl_get_molecule")
async def get_molecule(molecule_chembl_id: str) -> dict:
    """Get molecule (drug/compound) information from ChEMBL by ChEMBL ID.

    Args:
        molecule_chembl_id: ChEMBL molecule ID (e.g., 'CHEMBL2108041' for ocrelizumab)

    Returns:
        JSON with molecule details including name, type, max phase, approval date, and properties
    """
    logger.info(f"Tool invoked: get_molecule(molecule_chembl_id='{molecule_chembl_id}')")
    try:
        result = await chembl_client.get_molecule(molecule_chembl_id)
        logger.info(f"Tool succeeded: get_molecule(molecule_chembl_id='{molecule_chembl_id}')")
        return result
    except Exception as e:
        logger.error(
            f"Tool failed: get_molecule(molecule_chembl_id='{molecule_chembl_id}') - {e}",
            exc_info=True,
        )
        return f"Error calling ChEMBL API: {str(e)}"


@chembl_mcp.tool(name="chembl_search_molecules")
async def search_molecules(query: str, limit: int = 20) -> dict:
    """Search molecules (drugs/compounds) in ChEMBL by name or synonym.

    Args:
        query: Search query (molecule name or synonym, e.g., 'ocrelizumab')
        limit: Maximum number of results (default: 20)

    Returns:
        JSON with list of matching molecules
    """
    logger.info(f"Tool invoked: search_molecules(query='{query}', limit={limit})")
    try:
        result = await chembl_client.search_molecules(query, limit)
        logger.info(f"Tool succeeded: search_molecules(query='{query}')")
        return result
    except Exception as e:
        logger.error(
            f"Tool failed: search_molecules(query='{query}') - {e}",
            exc_info=True,
        )
        return f"Error calling ChEMBL API: {str(e)}"


@chembl_mcp.tool(name="chembl_get_target")
async def get_target(target_chembl_id: str) -> dict:
    """Get target (protein) information from ChEMBL by ChEMBL ID.

    Args:
        target_chembl_id: ChEMBL target ID (e.g., 'CHEMBL2058' for CD20)

    Returns:
        JSON with target details including name, type, and organism
    """
    logger.info(f"Tool invoked: get_target(target_chembl_id='{target_chembl_id}')")
    try:
        result = await chembl_client.get_target(target_chembl_id)
        logger.info(f"Tool succeeded: get_target(target_chembl_id='{target_chembl_id}')")
        return result
    except Exception as e:
        logger.error(
            f"Tool failed: get_target(target_chembl_id='{target_chembl_id}') - {e}",
            exc_info=True,
        )
        return f"Error calling ChEMBL API: {str(e)}"


@chembl_mcp.tool(name="chembl_search_targets")
async def search_targets(query: str, limit: int = 20) -> dict:
    """Search targets (proteins) in ChEMBL by name or synonym.

    Args:
        query: Search query (target name or synonym, e.g., 'CD20' or 'MS4A1')
        limit: Maximum number of results (default: 20)

    Returns:
        JSON with list of matching targets
    """
    logger.info(f"Tool invoked: search_targets(query='{query}', limit={limit})")
    try:
        result = await chembl_client.search_targets(query, limit)
        logger.info(f"Tool succeeded: search_targets(query='{query}')")
        return result
    except Exception as e:
        logger.error(
            f"Tool failed: search_targets(query='{query}') - {e}",
            exc_info=True,
        )
        return f"Error calling ChEMBL API: {str(e)}"


@chembl_mcp.tool(name="chembl_get_activities")
async def get_activities(
    target_chembl_id: str = None,
    molecule_chembl_id: str = None,
    limit: int = 50,
) -> dict:
    """Get bioactivity data from ChEMBL.

    IMPORTANT: Provide either target_chembl_id or molecule_chembl_id (or both) to filter results.
    If neither is provided, the query may return too many results.

    Args:
        target_chembl_id: Filter by ChEMBL target ID (optional)
        molecule_chembl_id: Filter by ChEMBL molecule ID (optional)
        limit: Maximum number of results (default: 50)

    Returns:
        JSON with activity data including standard_value, standard_type, and assay information
    """
    logger.info(
        f"Tool invoked: get_activities(target_chembl_id='{target_chembl_id}', molecule_chembl_id='{molecule_chembl_id}', limit={limit})"
    )
    try:
        result = await chembl_client.get_activities(target_chembl_id, molecule_chembl_id, limit)
        logger.info("Tool succeeded: get_activities()")
        return result
    except Exception as e:
        logger.error(f"Tool failed: get_activities() - {e}", exc_info=True)
        return f"Error calling ChEMBL API: {str(e)}"


@chembl_mcp.tool(name="chembl_get_mechanism")
async def get_mechanism(molecule_chembl_id: str) -> dict:
    """Get mechanism of action for a molecule from ChEMBL.

    Args:
        molecule_chembl_id: ChEMBL molecule ID

    Returns:
        JSON with mechanism data including target, action type, and mechanism description
    """
    logger.info(f"Tool invoked: get_mechanism(molecule_chembl_id='{molecule_chembl_id}')")
    try:
        result = await chembl_client.get_mechanism(molecule_chembl_id)
        logger.info(f"Tool succeeded: get_mechanism(molecule_chembl_id='{molecule_chembl_id}')")
        return result
    except Exception as e:
        logger.error(
            f"Tool failed: get_mechanism(molecule_chembl_id='{molecule_chembl_id}') - {e}",
            exc_info=True,
        )
        return f"Error calling ChEMBL API: {str(e)}"


@chembl_mcp.tool(name="chembl_find_drugs_by_target")
async def find_drugs_by_target(target_chembl_id: str, limit: int = 50) -> dict:
    """Find all drugs/compounds targeting a specific protein.

    Args:
        target_chembl_id: ChEMBL target ID
        limit: Maximum number of results (default: 50)

    Returns:
        JSON with list of molecules that target the specified protein
    """
    logger.info(
        f"Tool invoked: find_drugs_by_target(target_chembl_id='{target_chembl_id}', limit={limit})"
    )
    try:
        result = await chembl_client.find_drugs_by_target(target_chembl_id, limit)
        logger.info(f"Tool succeeded: find_drugs_by_target(target_chembl_id='{target_chembl_id}')")
        return result
    except Exception as e:
        logger.error(
            f"Tool failed: find_drugs_by_target(target_chembl_id='{target_chembl_id}') - {e}",
            exc_info=True,
        )
        return f"Error calling ChEMBL API: {str(e)}"


@chembl_mcp.tool(name="chembl_find_drugs_by_indication")
async def find_drugs_by_indication(disease_query: str, limit: int = 50) -> dict:
    """Find all drugs for a disease/indication.

    Args:
        disease_query: Disease name or MeSH heading (e.g., 'Multiple Sclerosis')
        limit: Maximum number of results (default: 50)

    Returns:
        JSON with list of drug-indication pairs
    """
    logger.info(
        f"Tool invoked: find_drugs_by_indication(disease_query='{disease_query}', limit={limit})"
    )
    try:
        result = await chembl_client.find_drugs_by_indication(disease_query, limit)
        logger.info(f"Tool succeeded: find_drugs_by_indication(disease_query='{disease_query}')")
        return result
    except Exception as e:
        logger.error(
            f"Tool failed: find_drugs_by_indication(disease_query='{disease_query}') - {e}",
            exc_info=True,
        )
        return f"Error calling ChEMBL API: {str(e)}"


@chembl_mcp.tool(name="chembl_get_drug_indications")
async def get_drug_indications(molecule_chembl_id: str) -> dict:
    """Get all indications (diseases) for a specific drug.

    Args:
        molecule_chembl_id: ChEMBL molecule ID

    Returns:
        JSON with list of indications for the drug
    """
    logger.info(
        f"Tool invoked: get_drug_indications(molecule_chembl_id='{molecule_chembl_id}')"
    )
    try:
        result = await chembl_client.get_drug_indications(molecule_chembl_id)
        logger.info(
            f"Tool succeeded: get_drug_indications(molecule_chembl_id='{molecule_chembl_id}')"
        )
        return result
    except Exception as e:
        logger.error(
            f"Tool failed: get_drug_indications(molecule_chembl_id='{molecule_chembl_id}') - {e}",
            exc_info=True,
        )
        return f"Error calling ChEMBL API: {str(e)}"

