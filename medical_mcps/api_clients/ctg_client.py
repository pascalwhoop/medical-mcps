"""
ClinicalTrials.gov API Client
Documentation: https://clinicaltrials.gov/api/v2/docs
Base URL: https://clinicaltrials.gov/api/v2
OpenAPI Spec: See notes/ctg-oas-v2.yaml

Note: Uses requests library instead of httpx because ClinicalTrials.gov API
blocks httpx's HTTP client signature but allows requests/urllib3.
"""

import asyncio
import json
import logging
from typing import Any

import requests
from hishel.requests import CacheAdapter

from .base_client import APIUpstreamError, BaseAPIClient

logger = logging.getLogger(__name__)

# Default fields for search operations to keep response sizes manageable
# These essential fields provide enough information for listing/searching studies
# without the massive overhead of full study details
DEFAULT_SEARCH_FIELDS = [
    "NCTId",
    "BriefTitle",
    "OfficialTitle",
    "OverallStatus",
    "Condition",
    "InterventionName",
    "Phase",
    "StartDate",
    "CompletionDate",
    "EnrollmentCount",
    "BriefSummary",
    "EligibilityCriteria",
    "LocationCity",
    "LocationCountry",
    "LeadSponsorName",
]

# Maximum response size in bytes (150KB) as safety net
# With default fields, responses should be much smaller, but this prevents edge cases
MAX_RESPONSE_SIZE_BYTES = 150 * 1024


class CTGClient(BaseAPIClient):
    """Client for interacting with the ClinicalTrials.gov REST API v2"""

    def __init__(self):
        super().__init__(
            base_url="https://clinicaltrials.gov/api/v2",
            api_name="ClinicalTrials.gov",
            timeout=60.0,  # CTG can be slow for complex queries
            rate_limit_delay=0.5,  # Conservative rate limiting
        )
        # Use requests.Session for connection pooling
        # Note: requests is synchronous, so we'll wrap calls in asyncio.to_thread
        self._session = requests.Session()
        self._session.timeout = self.timeout
        # Mount hishel CacheAdapter for HTTP caching only if enabled
        # Note: Disabled by default due to SQLite threading issues with asyncio.to_thread
        if self.enable_cache:
            self._session.mount("https://", CacheAdapter())
            self._session.mount("http://", CacheAdapter())
        # BaseAPIClient expects _client for context manager, but we use _session
        self._client = None  # Not used, but needed for BaseAPIClient compatibility

    async def _run_sync(self, func, *args, **kwargs):
        """Helper to run synchronous requests calls in a separate thread."""
        return await asyncio.to_thread(func, *args, **kwargs)

    async def _get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Make a GET request using requests library (which works with CTG API)
        """
        url = f"{self.base_url}{endpoint}"

        # Log HTTP request
        param_str = "&".join(f"{k}={v}" for k, v in (params or {}).items())
        request_url = f"{url}?{param_str}" if param_str else url
        logger.info(f"HTTP Request: GET {request_url}")

        try:
            # Run requests.get in thread pool
            response = await self._run_sync(self._session.get, url, params=params)
            response.raise_for_status()
            logger.info(f"HTTP Response: {response.status_code} {response.reason}")
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code >= 500:
                logger.warning("HTTP Response: %s %s", e.response.status_code, e.response.reason)
            else:
                logger.error(f"HTTP Response: {e.response.status_code} {e.response.reason}")
            error_msg = f"{self.api_name} API error: HTTP {e.response.status_code}"
            try:
                error_detail = e.response.json()
                if isinstance(error_detail, dict):
                    for field in ["error", "message", "detail", "error_message"]:
                        if field in error_detail:
                            error_msg += f" - {error_detail[field]}"
                            break
                    else:
                        error_msg += f" - {e!s}"
            except Exception:
                error_msg += f" - {e!s}"
            if e.response.status_code >= 500:
                raise APIUpstreamError(
                    error_msg,
                    status_code=e.response.status_code,
                    api_name=self.api_name,
                ) from e
            raise Exception(error_msg) from e
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP Error: {e!s}")
            raise Exception(f"{self.api_name} API error: {e!s}") from e

    async def search_studies(
        self,
        condition: str | None = None,
        intervention: str | None = None,
        term: str | None = None,
        status: list[str] | None = None,
        page_size: int = 20,
        page_token: str | None = None,
        fields: list[str] | None = None,
    ) -> dict:
        """
        Search clinical trials with various filters

        Args:
            condition: Condition/disease query (e.g., 'multiple sclerosis')
            intervention: Intervention/treatment query (e.g., 'ocrelizumab')
            term: General search terms
            status: List of statuses to filter (e.g., ['RECRUITING', 'COMPLETED'])
            page_size: Number of results per page (default: 20)
            page_token: Token for pagination (from previous response)
            fields: List of fields to return (None = all fields)

        Returns:
            Dict with study results and pagination info (includes metadata)
        """
        logger.info(
            f"Searching studies: condition={condition}, intervention={intervention}, status={status}"
        )

        params: dict[str, Any] = {
            "format": "json",
            "pageSize": page_size,
        }

        # Add query parameters
        if condition:
            params["query.cond"] = condition
        if intervention:
            params["query.intr"] = intervention
        if term:
            params["query.term"] = term

        # Add filters
        if status:
            params["filter.overallStatus"] = "|".join(status)

        # Add pagination
        if page_token:
            params["pageToken"] = page_token

        # Add field selection - use default fields if none specified
        # This dramatically reduces response size (from ~460KB to ~16-34KB for 20 studies)
        if fields is None:
            fields = DEFAULT_SEARCH_FIELDS
        if fields:
            params["fields"] = "|".join(fields)

        try:
            data = await self._get("/studies", params=params)

            # Build initial metadata
            metadata = {
                "page_size": page_size,
                "has_next_page": "nextPageToken" in data,
            }
            if "nextPageToken" in data:
                metadata["next_page_token"] = data["nextPageToken"]
            if "studies" in data:
                metadata["count"] = len(data["studies"])

            # Safety net: Check response size and truncate if necessary
            # This should rarely trigger with default fields, but protects against edge cases
            formatted_response = self.format_response(data, metadata)
            response_json = json.dumps(formatted_response)
            response_size = len(response_json.encode("utf-8"))

            original_count = len(data.get("studies", []))
            truncated = False

            if response_size > MAX_RESPONSE_SIZE_BYTES:
                logger.warning(
                    f"Response size ({response_size} bytes) exceeds limit ({MAX_RESPONSE_SIZE_BYTES} bytes). "
                    f"Truncating studies from {original_count} to fit within limit."
                )

                # Binary search to find max studies that fit
                studies = data.get("studies", [])
                low, high = 1, len(studies)
                max_fitting = 0

                while low <= high:
                    mid = (low + high) // 2
                    test_data = {**data, "studies": studies[:mid]}
                    test_metadata = {**metadata, "count": mid}
                    test_response = self.format_response(test_data, test_metadata)
                    test_json = json.dumps(test_response)
                    test_size = len(test_json.encode("utf-8"))

                    if test_size <= MAX_RESPONSE_SIZE_BYTES:
                        max_fitting = mid
                        low = mid + 1
                    else:
                        high = mid - 1

                if max_fitting > 0:
                    data["studies"] = studies[:max_fitting]
                    truncated = True
                    metadata["count"] = max_fitting
                else:
                    logger.error(
                        "Cannot fit even 1 study within size limit. Returning empty result."
                    )
                    data["studies"] = []
                    metadata["count"] = 0

            if truncated:
                metadata["truncated"] = True
                metadata["original_count"] = original_count
                metadata["warning"] = (
                    f"Response truncated from {original_count} to {len(data['studies'])} "
                    f"studies to fit within size limit"
                )

            return self.format_response(data, metadata)
        except Exception as e:
            logger.error(f"Error searching studies: {e}", exc_info=True)
            return self.format_response(None, {"error": f"ClinicalTrials.gov API error: {e!s}"})

    async def get_study(
        self,
        nct_id: str,
        fields: list[str] | None = None,
        format: str = "json",
    ) -> dict:
        """
        Get single study by NCT ID

        Args:
            nct_id: NCT identifier (e.g., 'NCT00841061')
            fields: List of fields to return (None = all fields)
            format: Response format ('json', 'csv', 'json.zip', 'fhir.json', 'ris')

        Returns:
            Dict with study data
        """
        logger.info(f"Getting study: {nct_id}")

        # Validate NCT ID format
        if not nct_id.upper().startswith("NCT"):
            return self.format_response(
                None,
                {
                    "error": f"Invalid NCT ID format: '{nct_id}'. Must start with 'NCT' (e.g., 'NCT00841061')"
                },
            )

        params: dict[str, Any] = {"format": format}
        if fields:
            params["fields"] = "|".join(fields)

        try:
            data = await self._get(f"/studies/{nct_id}", params=params)
            return self.format_response(data)
        except APIUpstreamError as e:
            return self.format_upstream_error(e, data=None)
        except Exception as e:
            if "404" in str(e) or "Not Found" in str(e):
                logger.info("Study %s not found", nct_id)
                return self.format_response(None, {"error": f"Study {nct_id} not found"})
            logger.error(f"Error getting study {nct_id}: {e}", exc_info=True)
            return self.format_response(None, {"error": f"ClinicalTrials.gov API error: {e!s}"})

    async def search_by_condition(
        self,
        condition_query: str,
        status: list[str] | None = None,
        page_size: int = 20,
    ) -> dict:
        """
        Search studies by condition/disease

        Args:
            condition_query: Condition or disease name (e.g., 'multiple sclerosis')
            status: List of statuses to filter (optional)
            page_size: Number of results per page (default: 20)

        Returns:
            JSON string with study results
        """
        logger.info(f"Searching by condition: {condition_query}")
        return await self.search_studies(
            condition=condition_query, status=status, page_size=page_size
        )

    async def search_by_intervention(
        self,
        intervention_query: str,
        condition: str | None = None,
        status: list[str] | None = None,
        page_size: int = 20,
    ) -> dict:
        """
        Search studies by intervention/treatment, optionally narrowed by condition.

        Args:
            intervention_query: Intervention or treatment name (e.g., 'ocrelizumab')
            condition: Optional disease/condition to AND-filter server-side (e.g., 'multiple sclerosis').
                Strongly recommended for high-fan-out drugs to avoid oversized payloads.
            status: List of statuses to filter (optional)
            page_size: Number of results per page (default: 20)

        Returns:
            JSON string with study results
        """
        logger.info(f"Searching by intervention: {intervention_query} (condition={condition})")
        return await self.search_studies(
            intervention=intervention_query,
            condition=condition,
            status=status,
            page_size=page_size,
        )

    async def get_study_metadata(self, include_indexed_only: bool = False) -> dict:
        """
        Get study data model metadata (available fields)

        Note: The CTG API v2 metadata endpoint may not be available or may require
        different parameters. This method attempts to retrieve metadata but may return
        an error if the endpoint is not accessible.

        Args:
            include_indexed_only: Include indexed-only fields (default: False)

        Returns:
            Dict with field metadata or error message
        """
        logger.info("Getting study metadata")
        # Try without params first, as the endpoint might not support them
        try:
            data = await self._get("/studies/metadata")
            return self.format_response(data)
        except Exception:
            # If that fails, try with params
            try:
                params = {"includeIndexedOnly": str(include_indexed_only).lower()}
                data = await self._get("/studies/metadata", params=params)
                return self.format_response(data)
            except Exception as e2:
                logger.warning(f"Metadata endpoint not available: {e2}. Returning error response.")
                return self.format_response(
                    None,
                    {
                        "error": "ClinicalTrials.gov metadata endpoint is not available or has changed. Please check the API documentation.",
                        "details": str(e2),
                    },
                )

    async def get_search_areas(self) -> dict:
        """
        Get search area documentation

        Returns:
            Dict with search area information
        """
        logger.info("Getting search areas")
        try:
            data = await self._get("/studies/search-areas")
            return self.format_response(data)
        except Exception as e:
            logger.error(f"Error getting search areas: {e}", exc_info=True)
            return self.format_response(None, {"error": f"ClinicalTrials.gov API error: {e!s}"})
