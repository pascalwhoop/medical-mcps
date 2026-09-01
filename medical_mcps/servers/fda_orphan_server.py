#!/usr/bin/env python3
"""FDA Orphan Drug MCP server."""

import logging

from ..api_clients.fda_orphan_client import FDAOrphanClient
from ..fastmcp_server import MedicalFastMCP as FastMCP
from ..med_mcp_server import tool as medmcps_tool
from ..med_mcp_server import unified_mcp

logger = logging.getLogger(__name__)

fda_orphan_mcp = FastMCP(
    "fda-orphan-api-server",
    stateless_http=True,
    json_response=True,
)

_client = FDAOrphanClient()


@medmcps_tool(name="fda_orphan_search_exclusivity", servers=[fda_orphan_mcp, unified_mcp])
async def fda_orphan_search_exclusivity(
    drug_name: str | None = None,
    active_ingredient: str | None = None,
    application_number: str | None = None,
) -> dict:
    """Search FDA Orange Book for orphan drug exclusivity (ODE) records.

    Returns applications with 7-year orphan market exclusivity grants.
    ODE code means the FDA approved the drug for an orphan indication and
    granted 7 years of market exclusivity. Use this to check whether a drug
    holds active orphan exclusivity that would block a competing product.

    For full orphan designation history (pre-approval designations), check
    the FDA OOPD website: https://www.accessdata.fda.gov/scripts/opdlisting/oopd/

    Args:
        drug_name: Brand or generic name (e.g., "gleevec" or "imatinib")
        active_ingredient: Active ingredient (e.g., "imatinib mesylate")
        application_number: NDA/BLA number (e.g., "NDA021588")
    """
    logger.info(
        "Tool invoked: fda_orphan_search_exclusivity(drug=%s, ingredient=%s)",
        drug_name,
        active_ingredient,
    )
    try:
        result = await _client.search_orphan_exclusivity(
            drug_name=drug_name,
            active_ingredient=active_ingredient,
            application_number=application_number,
        )
        logger.info("Tool succeeded: fda_orphan_search_exclusivity")
        return result
    except Exception as e:
        logger.error("Tool failed: fda_orphan_search_exclusivity - %s", e, exc_info=True)
        return {
            "api_source": "FDA_orange_book",
            "data": [],
            "error": f"FDA orphan exclusivity lookup error: {e!s}",
        }


@medmcps_tool(name="fda_orphan_search_oopd", servers=[fda_orphan_mcp, unified_mcp])
async def fda_orphan_search_oopd(
    drug_name: str | None = None,
    disease_name: str | None = None,
) -> dict:
    """Search the FDA Orphan Products Designation (OOPD) database.

    Returns orphan designation records including pre-approval designations,
    which the Orange Book ODE codes do not cover. The OOPD database is the
    authoritative source for orphan designations (e.g., ivacaftor has ~28 records).

    Searchable by drug, by disease/indication, or both (AND-filter). Use a
    disease search to find **competing molecules** with orphan designation for
    the proposed indication — they could attach 7-year ODE on approval and
    become first-mover for that indication.

    Args:
        drug_name: Drug or product name (e.g., "ivacaftor", "gleevec")
        disease_name: Disease / indication text (e.g., "cystinuria", "IgG4-related disease")

    At least one of drug_name or disease_name must be provided.
    """
    drug = drug_name.strip() if drug_name else None
    disease = disease_name.strip() if disease_name else None
    logger.info("Tool invoked: fda_orphan_search_oopd(drug=%s, disease=%s)", drug, disease)
    if not drug and not disease:
        return {
            "api_source": "FDA_OOPD",
            "data": [],
            "metadata": {"error": "Either drug_name or disease_name is required."},
        }
    try:
        result = await _client.search_oopd_designations(drug_name=drug, disease_name=disease)
        logger.info("Tool succeeded: fda_orphan_search_oopd")
        return result
    except Exception as e:
        logger.error("Tool failed: fda_orphan_search_oopd - %s", e, exc_info=True)
        return {
            "api_source": "FDA_OOPD",
            "data": [],
            "error": f"OOPD lookup error: {e!s}",
        }


@medmcps_tool(name="fda_orphan_get_application", servers=[fda_orphan_mcp, unified_mcp])
async def fda_orphan_get_application(
    drug_name: str | None = None,
    active_ingredient: str | None = None,
    application_number: str | None = None,
    limit: int = 25,
) -> dict:
    """Get FDA application details for a drug from the FDA drugsfda database.

    Returns the sponsoring NDA/BLA number, sponsor name, and product list.
    Use this alongside fda_orphan_search_exclusivity to identify whether
    the NDA holder has orphan exclusivity for a given indication.

    Args:
        drug_name: Brand or generic name (e.g., "gleevec")
        active_ingredient: Active ingredient (e.g., "imatinib")
        application_number: Full NDA/BLA number (e.g., "NDA021588")
        limit: Max results (default 25)
    """
    logger.info(
        "Tool invoked: fda_orphan_get_application(drug=%s, ingredient=%s)",
        drug_name,
        active_ingredient,
    )
    try:
        result = await _client.get_application_details(
            drug_name=drug_name,
            active_ingredient=active_ingredient,
            application_number=application_number,
            limit=limit,
        )
        logger.info("Tool succeeded: fda_orphan_get_application")
        return result
    except Exception as e:
        logger.error("Tool failed: fda_orphan_get_application - %s", e, exc_info=True)
        return {
            "api_source": "FDA_drugsfda",
            "data": [],
            "error": f"FDA orphan application lookup error: {e!s}",
        }
