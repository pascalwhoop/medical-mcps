"""
NCI Clinical Trials Search API Client
Documentation: https://clinicaltrialsapi.cancer.gov/api/v2
Requires API key from https://clinicaltrialsapi.cancer.gov/
"""

import json
import logging
import os
from typing import Any

from .base_client import BaseAPIClient

logger = logging.getLogger(__name__)

NCI_BASE_URL = "https://clinicaltrialsapi.cancer.gov/api/v2"
NCI_TRIALS_URL = f"{NCI_BASE_URL}/trials"


class NCIClient(BaseAPIClient):
    """Client for NCI Clinical Trials Search API."""

    def __init__(self, api_key: str | None = None):
        """Initialize NCI client.

        Args:
            api_key: NCI API key (or set NCI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("NCI_API_KEY")
        super().__init__(
            base_url=NCI_BASE_URL,
            api_name="NCI",
            timeout=60.0,
            rate_limit_delay=1.0,
        )

    def _get_headers(self) -> dict[str, str]:
        """Get headers with API key if available."""
        headers = {}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    async def search_trials(
        self,
        conditions: list[str] | None = None,
        interventions: list[str] | None = None,
        phase: str | None = None,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Search NCI clinical trials.

        Args:
            conditions: List of condition/disease names
            interventions: List of intervention names
            phase: Trial phase filter
            status: Recruiting status filter
            limit: Maximum number of results
            offset: Result offset for pagination

        Returns:
            Dict with trial search results
        """
        if not self.api_key:
            return self.format_response(
                [],
                {
                    "error": "NCI API key required. Get one at https://clinicaltrialsapi.cancer.gov/"
                },
            )

        params: dict[str, Any] = {
            "size": limit,
            "from": offset,
        }

        if conditions:
            params["primary_disease_names"] = conditions

        if interventions:
            params["intervention_names"] = interventions

        if phase:
            params["phase"] = phase

        if status:
            params["current_trial_status"] = status

        try:
            headers = self._get_headers()
            # Use full URL for NCI API with custom headers
            await self._rate_limit()
            response_text = await self.client.get(
                NCI_TRIALS_URL,
                params=params,
                headers=headers,
                timeout=self.timeout,
            )
            response_text.raise_for_status()
            response = json.loads(response_text.text)

            trials = response.get("data", [])
            total = response.get("total", len(trials))

            return self.format_response(
                trials,
                {
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                },
            )
        except Exception as e:
            logger.error(f"NCI trial search failed: {e}", exc_info=True)
            return self.format_response([], {"error": f"NCI API error: {str(e)}"})

    async def get_trial(self, trial_id: str) -> dict[str, Any]:
        """
        Get trial details by ID.

        Args:
            trial_id: NCI trial ID

        Returns:
            Dict with trial details
        """
        if not self.api_key:
            return self.format_response(
                None,
                {
                    "error": "NCI API key required. Get one at https://clinicaltrialsapi.cancer.gov/"
                },
            )

        try:
            headers = self._get_headers()
            await self._rate_limit()
            response_text = await self.client.get(
                f"{NCI_TRIALS_URL}/{trial_id}",
                headers=headers,
                timeout=self.timeout,
            )
            response_text.raise_for_status()
            response = json.loads(response_text.text)

            return self.format_response(response)
        except Exception as e:
            logger.error(f"Failed to fetch NCI trial {trial_id}: {e}", exc_info=True)
            return self.format_response(None, {"error": f"NCI API error: {str(e)}"})
