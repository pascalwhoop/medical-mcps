#!/usr/bin/env python3
"""
BioThings Suite API MCP Server
Exposes MyGene, MyDisease, and MyChem tools via MCP at /tools/biothings/mcp
"""

import logging

from mcp.server.fastmcp import FastMCP

from ..api_clients.mychem_client import MyChemClient
from ..api_clients.mydisease_client import MyDiseaseClient
from ..api_clients.mygene_client import MyGeneClient
from ..med_mcp_server import tool as medmcps_tool
from ..med_mcp_server import unified_mcp

logger = logging.getLogger(__name__)

mygene_client = MyGeneClient()
mydisease_client = MyDiseaseClient()
mychem_client = MyChemClient()

biothings_mcp = FastMCP(
    "biothings-api-server",
    stateless_http=True,
    json_response=True,
)


@medmcps_tool(name="mygene_get_gene", servers=[biothings_mcp, unified_mcp])
async def mygene_get_gene(
    gene_id_or_symbol: str, fields: list[str] | None = None
) -> dict:
    """Get gene information from MyGene.info by ID or symbol."""
    logger.info(
        f"Tool invoked: mygene_get_gene(gene_id_or_symbol='{gene_id_or_symbol}')"
    )
    try:
        result = await mygene_client.get_gene(gene_id_or_symbol, fields=fields)
        return result
    except Exception as e:
        logger.error(f"Tool failed: mygene_get_gene() - {e}", exc_info=True)
        return {"api_source": "MyGene", "data": None, "error": f"Error: {str(e)}"}


@medmcps_tool(name="mydisease_get_disease", servers=[biothings_mcp, unified_mcp])
async def mydisease_get_disease(
    disease_id_or_name: str, fields: list[str] | None = None
) -> dict:
    """Get disease information from MyDisease.info by ID or name."""
    logger.info(
        f"Tool invoked: mydisease_get_disease(disease_id_or_name='{disease_id_or_name}')"
    )
    try:
        result = await mydisease_client.get_disease(disease_id_or_name, fields=fields)
        return result
    except Exception as e:
        logger.error(f"Tool failed: mydisease_get_disease() - {e}", exc_info=True)
        return {"api_source": "MyDisease", "data": None, "error": f"Error: {str(e)}"}


@medmcps_tool(name="mychem_get_drug", servers=[biothings_mcp, unified_mcp])
async def mychem_get_drug(
    drug_id_or_name: str, fields: list[str] | None = None
) -> dict:
    """Get drug/chemical information from MyChem.info by ID or name."""
    logger.info(f"Tool invoked: mychem_get_drug(drug_id_or_name='{drug_id_or_name}')")
    try:
        result = await mychem_client.get_drug(drug_id_or_name, fields=fields)
        return result
    except Exception as e:
        logger.error(f"Tool failed: mychem_get_drug() - {e}", exc_info=True)
        return {"api_source": "MyChem", "data": None, "error": f"Error: {str(e)}"}
