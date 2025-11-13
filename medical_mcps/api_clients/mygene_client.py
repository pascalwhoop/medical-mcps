"""
MyGene.info API Client
Documentation: https://docs.mygene.info/
Provides gene annotations and information
"""

import json
import logging
from typing import Any
from urllib.parse import quote

from .base_client import BaseAPIClient

logger = logging.getLogger(__name__)

MYGENE_BASE_URL = "https://mygene.info/v3"
MYGENE_QUERY_URL = f"{MYGENE_BASE_URL}/query"
MYGENE_GET_URL = f"{MYGENE_BASE_URL}/gene"


class MyGeneClient(BaseAPIClient):
    """Client for MyGene.info API."""

    def __init__(self):
        """Initialize MyGene client."""
        super().__init__(
            base_url=MYGENE_BASE_URL,
            api_name="MyGene",
            timeout=60.0,
            rate_limit_delay=0.5,
        )

    async def get_gene(
        self, gene_id_or_symbol: str, fields: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Get gene information by ID or symbol.

        Args:
            gene_id_or_symbol: Gene ID (Entrez, Ensembl) or symbol (e.g., 'TP53', '7157')
            fields: Optional list of fields to return

        Returns:
            Dict with gene information
        """
        try:
            # If numeric, try direct GET
            if gene_id_or_symbol.isdigit():
                params = {}
                if fields:
                    params["fields"] = ",".join(fields)
                response = await self._request("GET", url=f"{MYGENE_GET_URL}/{gene_id_or_symbol}", params=params, return_json=False)
                data = json.loads(response)
                return self.format_response(data)

            # For symbols, query first
            params = {
                "q": f"symbol:{quote(gene_id_or_symbol)}",
                "species": "human",
                "size": 5,
            }
            if fields:
                params["fields"] = ",".join(fields)

            response = await self._request("GET", url=MYGENE_QUERY_URL, params=params, return_json=False)
            data = json.loads(response)

            hits = data.get("hits", [])
            # Filter for human genes (taxid 9606)
            human_hits = [h for h in hits if h.get("taxid") == 9606]
            best_hit = (human_hits[0] if human_hits else hits[0]) if hits else None

            if not best_hit:
                return self.format_response(
                    None, {"error": f"Gene '{gene_id_or_symbol}' not found"}
                )

            # Get full details by ID
            gene_id = best_hit.get("_id")
            if gene_id:
                full_response = await self._request("GET", url=f"{MYGENE_GET_URL}/{gene_id}", params={}, return_json=False)
                full_data = json.loads(full_response)
                return self.format_response(full_data)

            return self.format_response(best_hit)
        except Exception as e:
            logger.error(
                f"Failed to fetch gene {gene_id_or_symbol}: {e}", exc_info=True
            )
            return self.format_response(None, {"error": f"MyGene API error: {str(e)}"})
