#!/usr/bin/env python3
"""
ChEMBL API MCP Server
Exposes ChEMBL API tools via MCP at /tools/chembl/mcp
"""

import logging

from ..api_clients.chembl_client import ChEMBLClient
from ..fastmcp_server import MedicalFastMCP as FastMCP
from ..med_mcp_server import tool as medmcps_tool
from ..med_mcp_server import unified_mcp
from ..models.chembl import (
    ChEMBLActivity,
    ChEMBLDrugIndication,
    ChEMBLMechanism,
    ChEMBLMolecule,
    ChEMBLTarget,
)
from .validation import validate_list_response, validate_response

logger = logging.getLogger(__name__)

# Initialize API client
chembl_client = ChEMBLClient()

# Create FastMCP server for ChEMBL
chembl_mcp = FastMCP(
    "chembl-api-server",
    stateless_http=True,
    json_response=True,
)


@medmcps_tool(name="chembl_get_molecule", servers=[chembl_mcp, unified_mcp])
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
        result = validate_response(
            result,
            ChEMBLMolecule,
            key_field="molecule_chembl_id",
            api_name="ChEMBL",
            context=molecule_chembl_id,
        )
        logger.info(f"Tool succeeded: get_molecule(molecule_chembl_id='{molecule_chembl_id}')")
        return result
    except Exception as e:
        logger.error(
            f"Tool failed: get_molecule(molecule_chembl_id='{molecule_chembl_id}') - {e}",
            exc_info=True,
        )
        return f"Error calling ChEMBL API: {e!s}"


@medmcps_tool(name="chembl_search_molecules", servers=[chembl_mcp, unified_mcp])
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
        result = validate_list_response(
            result,
            ChEMBLMolecule,
            list_key="data",
            api_name="ChEMBL",
        )
        logger.info(f"Tool succeeded: search_molecules(query='{query}')")
        return result
    except Exception as e:
        logger.error(
            f"Tool failed: search_molecules(query='{query}') - {e}",
            exc_info=True,
        )
        return f"Error calling ChEMBL API: {e!s}"


@medmcps_tool(name="chembl_get_target", servers=[chembl_mcp, unified_mcp])
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
        result = validate_response(
            result,
            ChEMBLTarget,
            key_field="target_chembl_id",
            api_name="ChEMBL",
            context=target_chembl_id,
        )
        logger.info(f"Tool succeeded: get_target(target_chembl_id='{target_chembl_id}')")
        return result
    except Exception as e:
        logger.error(
            f"Tool failed: get_target(target_chembl_id='{target_chembl_id}') - {e}",
            exc_info=True,
        )
        return f"Error calling ChEMBL API: {e!s}"


@medmcps_tool(name="chembl_search_targets", servers=[chembl_mcp, unified_mcp])
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
        result = validate_list_response(
            result,
            ChEMBLTarget,
            list_key="data",
            api_name="ChEMBL",
        )
        logger.info(f"Tool succeeded: search_targets(query='{query}')")
        return result
    except Exception as e:
        logger.error(
            f"Tool failed: search_targets(query='{query}') - {e}",
            exc_info=True,
        )
        return f"Error calling ChEMBL API: {e!s}"


@medmcps_tool(name="chembl_get_activities", servers=[chembl_mcp, unified_mcp])
async def get_activities(
    target_chembl_id: str | None = None,
    molecule_chembl_id: str | None = None,
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
        result = validate_list_response(
            result,
            ChEMBLActivity,
            list_key="data",
            api_name="ChEMBL",
        )
        logger.info("Tool succeeded: get_activities()")
        return result
    except Exception as e:
        logger.error(f"Tool failed: get_activities() - {e}", exc_info=True)
        return f"Error calling ChEMBL API: {e!s}"


@medmcps_tool(name="chembl_get_mechanism", servers=[chembl_mcp, unified_mcp])
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
        result = validate_list_response(
            result,
            ChEMBLMechanism,
            list_key="data",
            api_name="ChEMBL",
        )
        logger.info(f"Tool succeeded: get_mechanism(molecule_chembl_id='{molecule_chembl_id}')")
        return result
    except Exception as e:
        logger.error(
            f"Tool failed: get_mechanism(molecule_chembl_id='{molecule_chembl_id}') - {e}",
            exc_info=True,
        )
        return f"Error calling ChEMBL API: {e!s}"


@medmcps_tool(name="chembl_find_drugs_by_target", servers=[chembl_mcp, unified_mcp])
async def find_drugs_by_target(
    target_chembl_id: str | None = None,
    target_name: str | None = None,
    limit: int = 50,
    max_results: int | None = None,
) -> dict:
    """Find all drugs/compounds targeting a specific protein.

    Args:
        target_chembl_id: ChEMBL target ID
        target_name: Target name or synonym to resolve when target_chembl_id is omitted
        limit: Maximum number of results (default: 50)
        max_results: Alias for limit

    Returns:
        JSON with list of molecules that target the specified protein
    """
    resolved_limit = max_results if max_results is not None else limit
    resolved_id = target_chembl_id
    if not resolved_id and target_name:
        search = await chembl_client.search_targets(target_name, limit=1)
        targets = search.get("data", []) if isinstance(search, dict) else []
        if targets and isinstance(targets[0], dict):
            resolved_id = targets[0].get("target_chembl_id")
    if not resolved_id:
        return {
            "api_source": "ChEMBL",
            "data": [],
            "metadata": {"error": "Either target_chembl_id or target_name is required"},
        }
    logger.info(
        f"Tool invoked: find_drugs_by_target(target_chembl_id='{resolved_id}', limit={resolved_limit})"
    )
    try:
        result = await chembl_client.find_drugs_by_target(resolved_id, resolved_limit)
        result = validate_list_response(
            result,
            ChEMBLMolecule,
            list_key="data",
            api_name="ChEMBL",
        )
        logger.info(f"Tool succeeded: find_drugs_by_target(target_chembl_id='{resolved_id}')")
        return result
    except Exception as e:
        logger.error(
            f"Tool failed: find_drugs_by_target(target_chembl_id='{resolved_id}') - {e}",
            exc_info=True,
        )
        return f"Error calling ChEMBL API: {e!s}"


@medmcps_tool(name="chembl_find_drugs_by_indication", servers=[chembl_mcp, unified_mcp])
async def find_drugs_by_indication(
    disease_query: str | None = None,
    indication: str | None = None,
    limit: int = 50,
    max_results: int | None = None,
) -> dict:
    """Find all drugs for a disease/indication.

    Args:
        disease_query: Disease name or MeSH heading (e.g., 'Multiple Sclerosis')
        indication: Alias for disease_query
        limit: Maximum number of results (default: 50)
        max_results: Alias for limit

    Returns:
        JSON with list of drug-indication pairs
    """
    resolved_query = disease_query or indication
    resolved_limit = max_results if max_results is not None else limit
    if not resolved_query:
        return {
            "api_source": "ChEMBL",
            "data": [],
            "metadata": {"error": "Either disease_query or indication is required"},
        }
    logger.info(
        f"Tool invoked: find_drugs_by_indication(disease_query='{resolved_query}', limit={resolved_limit})"
    )
    try:
        result = await chembl_client.find_drugs_by_indication(resolved_query, resolved_limit)
        result = validate_list_response(
            result,
            ChEMBLDrugIndication,
            list_key="data",
            api_name="ChEMBL",
        )
        logger.info(f"Tool succeeded: find_drugs_by_indication(disease_query='{resolved_query}')")
        return result
    except Exception as e:
        logger.error(
            f"Tool failed: find_drugs_by_indication(disease_query='{resolved_query}') - {e}",
            exc_info=True,
        )
        return f"Error calling ChEMBL API: {e!s}"


@medmcps_tool(name="chembl_get_drug_indications", servers=[chembl_mcp, unified_mcp])
async def get_drug_indications(molecule_chembl_id: str) -> dict:
    """Get all indications (diseases) for a specific drug.

    Args:
        molecule_chembl_id: ChEMBL molecule ID

    Returns:
        JSON with list of indications for the drug
    """
    logger.info(f"Tool invoked: get_drug_indications(molecule_chembl_id='{molecule_chembl_id}')")
    try:
        result = await chembl_client.get_drug_indications(molecule_chembl_id)
        result = validate_list_response(
            result,
            ChEMBLDrugIndication,
            list_key="data",
            api_name="ChEMBL",
        )
        logger.info(
            f"Tool succeeded: get_drug_indications(molecule_chembl_id='{molecule_chembl_id}')"
        )
        return result
    except Exception as e:
        logger.error(
            f"Tool failed: get_drug_indications(molecule_chembl_id='{molecule_chembl_id}') - {e}",
            exc_info=True,
        )
        return f"Error calling ChEMBL API: {e!s}"
