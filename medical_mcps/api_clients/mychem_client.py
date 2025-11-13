"""
MyChem.info API Client
Documentation: https://docs.mychem.info/
Provides drug/chemical annotations and information
"""

import json
import logging
from typing import Any
from urllib.parse import quote

from .base_client import BaseAPIClient

logger = logging.getLogger(__name__)

MYCHEM_BASE_URL = "https://mychem.info/v1"
MYCHEM_QUERY_URL = f"{MYCHEM_BASE_URL}/query"
MYCHEM_GET_URL = f"{MYCHEM_BASE_URL}/chem"


class MyChemClient(BaseAPIClient):
    """Client for MyChem.info API."""

    def __init__(self):
        """Initialize MyChem client."""
        super().__init__(
            base_url=MYCHEM_BASE_URL,
            api_name="MyChem",
            timeout=60.0,
            rate_limit_delay=0.5,
        )

    async def get_drug(
        self, drug_id_or_name: str, fields: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Get drug/chemical information by ID or name.

        Args:
            drug_id_or_name: Drug ID (DrugBank, ChEMBL, PubChem) or name (e.g., 'imatinib', 'DB00619')
            fields: Optional list of fields to return

        Returns:
            Dict with drug information
        """
        try:
            # Check if it's a known ID format
            if (
                drug_id_or_name.startswith("DB")
                or drug_id_or_name.startswith("CHEMBL")
                or drug_id_or_name.isdigit()
            ):
                params = {}
                if fields:
                    params["fields"] = ",".join(fields)
                response = await self._request("GET", url=f"{MYCHEM_GET_URL}/{drug_id_or_name}", params=params, return_json=False)
                data = json.loads(response)
                return self.format_response(data)

            # For names, query first
            params = {
                "q": f'name:"{quote(drug_id_or_name)}"',
                "size": 5,
            }
            if fields:
                params["fields"] = ",".join(fields)

            response = await self._request("GET", url=MYCHEM_QUERY_URL, params=params, return_json=False)
            data = json.loads(response)

            hits = data.get("hits", [])
            best_hit = hits[0] if hits else None

            if not best_hit:
                return self.format_response(
                    None, {"error": f"Drug '{drug_id_or_name}' not found"}
                )

            # Get full details by ID
            drug_id = best_hit.get("_id")
            if drug_id:
                full_response = await self._request("GET", url=f"{MYCHEM_GET_URL}/{drug_id}", params={}, return_json=False)
                full_data = json.loads(full_response)
                return self.format_response(full_data)

            return self.format_response(best_hit)
        except Exception as e:
            logger.error(f"Failed to fetch drug {drug_id_or_name}: {e}", exc_info=True)
            return self.format_response(None, {"error": f"MyChem API error: {str(e)}"})
