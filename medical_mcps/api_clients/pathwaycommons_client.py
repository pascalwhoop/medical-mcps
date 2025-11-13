"""
Pathway Commons API Client
Documentation: https://www.pathwaycommons.org/pc2/
Base URL: https://www.pathwaycommons.org/pc2
"""

import logging
from typing import Any

import httpx

from .base_client import BaseAPIClient

logger = logging.getLogger(__name__)


class PathwayCommonsClient(BaseAPIClient):
    """Client for interacting with the Pathway Commons API"""

    def __init__(self):
        super().__init__(
            base_url="https://www.pathwaycommons.org/pc2",
            api_name="Pathway Commons",
            timeout=160.0,  # 120s observed + 30% buffer - Pathway Commons API is very slow
        )

    async def _get_flexible(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> Any:
        """Make a GET request that handles both JSON and text responses"""
        url = f"{self.base_url}{endpoint}"

        # Log HTTP request
        param_str = "&".join(f"{k}={v}" for k, v in (params or {}).items())
        request_url = f"{url}?{param_str}" if param_str else url
        logger.info(f"HTTP Request: GET {request_url}")

        try:
            await self._rate_limit()
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            logger.info(
                f"HTTP Response: {response.status_code} {response.reason_phrase}"
            )
            # Pathway Commons returns various formats
            content_type = response.headers.get("content-type", "")
            if "json" in content_type:
                return response.json()
            else:
                return response.text
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP Response: {e.response.status_code} {e.response.reason_phrase}"
            )
            raise Exception(
                f"{self.api_name} API error: HTTP {e.response.status_code} - {str(e)}"
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"HTTP Error: {str(e)}")
            raise Exception(f"{self.api_name} API error: {str(e)}") from e

    async def search(
        self,
        q: str,
        type: str = "Pathway",
        format: str = "json",
        page: int = 0,
        datasource: str | None = None,
    ) -> dict:
        """
        Search Pathway Commons using v2 POST API

        Args:
            q: Search query
            type: Entity type ('Pathway', 'Protein', 'Gene', etc.)
            format: Response format ('json', 'xml', 'biopax')
            page: Page number
            datasource: Data source filter (e.g., 'Reactome', 'KEGG')

        Returns:
            Dict with search results (includes metadata)
        """
        # v2 API requires POST with JSON body
        payload: dict[str, Any] = {"q": q, "type": type}
        if datasource:
            payload["datasource"] = (
                [datasource] if isinstance(datasource, str) else datasource
            )

        data = await self._request("POST", endpoint="/v2/search", json_data=payload)
        return self.format_response(data, {"page": page})

    async def get_pathway(self, uri: str, format: str = "json") -> dict | str:
        """
        Get pathway information by URI

        Args:
            uri: Pathway URI (e.g., 'http://identifiers.org/reactome/R-HSA-1640170')
            format: Response format ('json', 'xml', 'biopax')

        Returns:
            Dict for JSON format, str for text formats (xml, biopax)
        """
        params = {"uri": uri, "format": format}
        data = await self._get_flexible("/get", params=params)
        return self.format_response(data)

    async def top_pathways(
        self, gene: str | None = None, datasource: str | None = None, limit: int = 10
    ) -> dict:
        """
        Get top pathways using v2 POST API

        Args:
            gene: Gene symbol or ID (optional) - used as query string
            datasource: Data source filter (optional)
            limit: Maximum number of results

        Returns:
            Dict with top pathways (includes metadata)
        """
        # v2 API requires POST with JSON body
        # The API requires 'q' parameter (query string), not 'gene'
        # If no gene provided, use '*' to get all top pathways
        payload: dict[str, Any] = {
            "q": gene if gene else "*"
        }
        if datasource:
            payload["datasource"] = (
                [datasource] if isinstance(datasource, str) else datasource
            )

        data = await self._request("POST", endpoint="/v2/top_pathways", json_data=payload)
        return self.format_response(data, {"limit": limit})

    async def graph(
        self,
        source: str,
        target: str | None = None,
        kind: str = "neighborhood",
        limit: int = 1,
        format: str = "json",
    ) -> dict | str:
        """
        Get pathway graph/network using v2 POST API

        Args:
            source: Source entity (gene/protein ID or URI)
            target: Target entity (optional, only for PATHSFROMTO)
            kind: Graph kind ('neighborhood', 'pathsbetween', 'pathsfromto', 'commonstream')
            limit: Path length limit
            format: Response format ('json', 'sif', 'txt', 'biopax', 'jsonld')

        Returns:
            Dict for JSON/jsonld format, str for text formats (sif, txt, biopax)
        """
        # Map kind to v2 endpoint
        kind_upper = kind.upper()
        if kind_upper == "NEIGHBORHOOD":
            endpoint = "/v2/neighborhood"
        elif kind_upper == "PATHSBETWEEN":
            endpoint = "/v2/pathsbetween"
        elif kind_upper == "PATHSFROMTO":
            endpoint = "/v2/pathsfromto"
        elif kind_upper == "COMMONSTREAM":
            endpoint = "/v2/commonstream"
        else:
            endpoint = "/v2/neighborhood"  # default

        # v2 API requires POST with JSON body
        payload: dict[str, Any] = {
            "source": [source],
            "format": format.upper()
            if format.upper() in ["BIOPAX", "SIF", "TXT", "GSEA", "SBGN", "JSONLD"]
            else "JSONLD",
            "limit": limit,
        }
        if target:
            payload["target"] = [target]

        data = await self._request("POST", endpoint=endpoint, json_data=payload)
        return self.format_response(data, {"kind": kind, "limit": limit})

    async def traverse(self, uri: str, path: str, format: str = "json") -> dict | str:
        """
        Traverse pathway data using v2 POST API

        Args:
            uri: Pathway or entity URI
            path: Traversal path (e.g., 'Pathway/pathwayComponent:Interaction/participant*/displayName')
            format: Response format ('json', 'xml')

        Returns:
            Dict for JSON format, str for XML format
        """
        # v2 API requires POST with JSON body
        payload: dict[str, Any] = {"uri": [uri], "path": path}

        data = await self._request("POST", endpoint="/v2/traverse", json_data=payload)
        return self.format_response(data)
