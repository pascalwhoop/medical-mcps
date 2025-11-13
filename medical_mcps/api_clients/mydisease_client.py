"""
MyDisease.info API Client
Documentation: https://docs.mydisease.info/
Provides disease ontology and synonyms
"""

import json
import logging
from typing import Any
from urllib.parse import quote

from .base_client import BaseAPIClient

logger = logging.getLogger(__name__)

MYDISEASE_BASE_URL = "https://mydisease.info/v1"
MYDISEASE_QUERY_URL = f"{MYDISEASE_BASE_URL}/query"
MYDISEASE_GET_URL = f"{MYDISEASE_BASE_URL}/disease"


class MyDiseaseClient(BaseAPIClient):
    """Client for MyDisease.info API."""

    def __init__(self):
        """Initialize MyDisease client."""
        super().__init__(
            base_url=MYDISEASE_BASE_URL,
            api_name="MyDisease",
            timeout=60.0,
            rate_limit_delay=0.5,
        )

    async def get_disease(
        self, disease_id_or_name: str, fields: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Get disease information by ID or name.

        Args:
            disease_id_or_name: Disease ID (MONDO, DOID) or name (e.g., 'melanoma', 'MONDO:0016575')
            fields: Optional list of fields to return

        Returns:
            Dict with disease information
        """
        try:
            # Check if it's a MONDO or DOID ID
            if disease_id_or_name.startswith("MONDO:") or disease_id_or_name.startswith(
                "DOID:"
            ):
                params = {}
                if fields:
                    params["fields"] = ",".join(fields)
                response = await self._request("GET", url=f"{MYDISEASE_GET_URL}/{disease_id_or_name}", params=params, return_json=False)
                data = json.loads(response)
                return self.format_response(data)

            # For names, query first
            params = {
                "q": f'name:"{quote(disease_id_or_name)}"',
                "size": 5,
            }
            if fields:
                params["fields"] = ",".join(fields)

            response = await self._request("GET", url=MYDISEASE_QUERY_URL, params=params, return_json=False)
            data = json.loads(response)

            hits = data.get("hits", [])
            best_hit = hits[0] if hits else None

            if not best_hit:
                return self.format_response(
                    None, {"error": f"Disease '{disease_id_or_name}' not found"}
                )

            # Get full details by ID
            disease_id = best_hit.get("_id")
            if disease_id:
                full_response = await self._request("GET", url=f"{MYDISEASE_GET_URL}/{disease_id}", params={}, return_json=False)
                full_data = json.loads(full_response)
                return self.format_response(full_data)

            return self.format_response(best_hit)
        except Exception as e:
            logger.error(
                f"Failed to fetch disease {disease_id_or_name}: {e}", exc_info=True
            )
            return self.format_response(
                None, {"error": f"MyDisease API error: {str(e)}"}
            )
