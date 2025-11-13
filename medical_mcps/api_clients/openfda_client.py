"""
OpenFDA API Client
Documentation: https://open.fda.gov/apis/
Provides access to FDA adverse event reports, drug labels, device events, etc.
"""

import json
import logging
import re
from typing import Any

from .base_client import BaseAPIClient

logger = logging.getLogger(__name__)

# OpenFDA API endpoints
OPENFDA_BASE_URL = "https://api.fda.gov"
OPENFDA_DRUG_EVENTS_URL = f"{OPENFDA_BASE_URL}/drug/event.json"
OPENFDA_DRUG_LABELS_URL = f"{OPENFDA_BASE_URL}/drug/label.json"
OPENFDA_DEVICE_EVENTS_URL = f"{OPENFDA_BASE_URL}/device/event.json"

# API limits
OPENFDA_DEFAULT_LIMIT = 25
OPENFDA_MAX_LIMIT = 100


def sanitize_input(text: str, max_length: int = 200) -> str:
    """Sanitize input to prevent injection attacks."""
    # Remove potentially dangerous characters
    text = re.sub(r'[<>"\';\\]', "", text)
    # Limit length
    text = text[:max_length]
    return text.strip()


class OpenFDAClient(BaseAPIClient):
    """Client for OpenFDA API."""

    def __init__(self):
        """Initialize OpenFDA client."""
        super().__init__(
            base_url=OPENFDA_BASE_URL,
            api_name="OpenFDA",
            timeout=60.0,
            rate_limit_delay=1.5,  # Conservative rate limiting (40/min without key)
        )

    def _build_adverse_event_query(
        self, drug: str | None, reaction: str | None, serious: bool | None
    ) -> str:
        """Build search query for adverse events."""
        search_parts = []

        if drug:
            drug_sanitized = sanitize_input(drug, max_length=100)
            if drug_sanitized:
                drug_query = (
                    f'(patient.drug.medicinalproduct:"{drug_sanitized}" OR '
                    f'patient.drug.openfda.brand_name:"{drug_sanitized}" OR '
                    f'patient.drug.openfda.generic_name:"{drug_sanitized}")'
                )
                search_parts.append(drug_query)

        if reaction:
            reaction_sanitized = sanitize_input(reaction, max_length=200)
            if reaction_sanitized:
                search_parts.append(
                    f'patient.reaction.reactionmeddrapt:"{reaction_sanitized}"'
                )

        if serious is not None:
            serious_value = "1" if serious else "2"
            search_parts.append(f"serious:{serious_value}")

        return " AND ".join(search_parts)

    async def search_adverse_events(
        self,
        drug: str | None = None,
        reaction: str | None = None,
        serious: bool | None = None,
        limit: int = OPENFDA_DEFAULT_LIMIT,
        page: int = 1,
        api_key: str | None = None,
    ) -> dict[str, Any]:
        """
        Search FDA adverse event reports (FAERS).

        Args:
            drug: Drug name to search for
            reaction: Adverse reaction term to search for
            serious: Filter for serious events only
            limit: Maximum number of results per page
            page: Page number (1-based)
            api_key: Optional OpenFDA API key

        Returns:
            Dict with adverse event results
        """
        if not drug and not reaction:
            return self.format_response(
                [],
                {
                    "error": "Please specify either a drug name or reaction term to search adverse events"
                },
            )

        search_query = self._build_adverse_event_query(drug, reaction, serious)
        skip = (page - 1) * limit

        params = {
            "search": search_query,
            "limit": min(limit, OPENFDA_MAX_LIMIT),
            "skip": skip,
        }

        if api_key:
            params["api_key"] = api_key

        try:
            # Use full URL for OpenFDA endpoints
            response = await self._request("GET", url=OPENFDA_DRUG_EVENTS_URL, params=params, return_json=False)
            response = json.loads(response)

            results = response.get("results", [])
            meta = response.get("meta", {})
            results_meta = meta.get("results", {})
            total = results_meta.get("total", len(results))

            # Format results
            formatted_results = []
            for result in results:
                patient = result.get("patient", {})
                drugs = patient.get("drug", [])
                reactions = patient.get("reaction", [])

                formatted_results.append(
                    {
                        "safetyreportid": result.get("safetyreportid"),
                        "serious": result.get("serious"),
                        "receivedate": result.get("receivedate"),
                        "drugs": [
                            {
                                "medicinalproduct": d.get("medicinalproduct"),
                                "drugindication": d.get("drugindication"),
                            }
                            for d in drugs[:3]  # Limit to first 3 drugs
                        ],
                        "reactions": [
                            r.get("reactionmeddrapt")
                            for r in reactions[:5]  # Limit to first 5 reactions
                        ],
                    }
                )

            return self.format_response(
                formatted_results,
                {
                    "total": total,
                    "page": page,
                    "page_size": limit,
                    "drug": drug,
                    "reaction": reaction,
                    "serious": serious,
                },
            )
        except Exception as e:
            logger.error(f"Adverse event search failed: {e}", exc_info=True)
            return self.format_response([], {"error": f"OpenFDA API error: {str(e)}"})

    async def get_adverse_event(
        self, report_id: str, api_key: str | None = None
    ) -> dict[str, Any]:
        """
        Get detailed adverse event report.

        Args:
            report_id: Safety report ID
            api_key: Optional OpenFDA API key

        Returns:
            Dict with detailed report information
        """
        params = {
            "search": f'safetyreportid:"{report_id}"',
            "limit": 1,
        }

        if api_key:
            params["api_key"] = api_key

        try:
            # Use full URL for OpenFDA endpoints
            response = await self._request("GET", url=OPENFDA_DRUG_EVENTS_URL, params=params, return_json=False)
            response = json.loads(response)

            results = response.get("results", [])
            if not results:
                return self.format_response(
                    None, {"error": f"Adverse event report '{report_id}' not found"}
                )

            result = results[0]
            patient = result.get("patient", {})

            return self.format_response(
                {
                    "safetyreportid": result.get("safetyreportid"),
                    "serious": result.get("serious"),
                    "receivedate": result.get("receivedate"),
                    "patient": {
                        "age": patient.get("patientonsetage"),
                        "sex": patient.get("patientsex"),
                        "drugs": patient.get("drug", []),
                        "reactions": patient.get("reaction", []),
                    },
                    "summary": result.get("summary", {}).get("narrative"),
                }
            )
        except Exception as e:
            logger.error(
                f"Failed to fetch adverse event {report_id}: {e}", exc_info=True
            )
            return self.format_response(None, {"error": f"OpenFDA API error: {str(e)}"})

    async def search_drug_labels(
        self,
        drug_name: str | None = None,
        indication: str | None = None,
        section: str | None = None,
        limit: int = OPENFDA_DEFAULT_LIMIT,
        page: int = 1,
        api_key: str | None = None,
    ) -> dict[str, Any]:
        """
        Search FDA drug labels (SPL).

        Args:
            drug_name: Drug name to search for
            indication: Search for drugs indicated for this condition
            section: Specific label section to search
            limit: Maximum number of results per page
            page: Page number (1-based)
            api_key: Optional OpenFDA API key

        Returns:
            Dict with drug label results
        """
        search_parts = []

        if drug_name:
            drug_sanitized = sanitize_input(drug_name, max_length=100)
            if drug_sanitized:
                search_parts.append(
                    f'(openfda.brand_name:"{drug_sanitized}" OR '
                    f'openfda.generic_name:"{drug_sanitized}")'
                )

        if indication:
            indication_sanitized = sanitize_input(indication, max_length=200)
            if indication_sanitized:
                search_parts.append(f'indications_and_usage:"{indication_sanitized}"')

        if section:
            section_sanitized = sanitize_input(section, max_length=50)
            if section_sanitized:
                search_parts.append(f'{section_sanitized}:"*"')

        if not search_parts:
            return self.format_response(
                [], {"error": "Please specify at least one search parameter"}
            )

        search_query = " AND ".join(search_parts)
        skip = (page - 1) * limit

        params = {
            "search": search_query,
            "limit": min(limit, OPENFDA_MAX_LIMIT),
            "skip": skip,
        }

        if api_key:
            params["api_key"] = api_key

        try:
            # Use full URL for OpenFDA endpoints
            response = await self._request("GET", url=OPENFDA_DRUG_LABELS_URL, params=params, return_json=False)
            response = json.loads(response)

            results = response.get("results", [])
            meta = response.get("meta", {})
            results_meta = meta.get("results", {})
            total = results_meta.get("total", len(results))

            # Format results
            formatted_results = []
            for result in results:
                openfda = result.get("openfda", {})
                formatted_results.append(
                    {
                        "set_id": result.get("id"),
                        "brand_name": openfda.get("brand_name", [None])[0]
                        if openfda.get("brand_name")
                        else None,
                        "generic_name": openfda.get("generic_name", [None])[0]
                        if openfda.get("generic_name")
                        else None,
                        "indications_and_usage": result.get(
                            "indications_and_usage", [None]
                        )[0]
                        if result.get("indications_and_usage")
                        else None,
                        "boxed_warning": result.get("boxed_warning", [None])[0]
                        if result.get("boxed_warning")
                        else None,
                    }
                )

            return self.format_response(
                formatted_results,
                {
                    "total": total,
                    "page": page,
                    "page_size": limit,
                },
            )
        except Exception as e:
            logger.error(f"Drug label search failed: {e}", exc_info=True)
            return self.format_response([], {"error": f"OpenFDA API error: {str(e)}"})

    async def get_drug_label(
        self, set_id: str, sections: list[str] | None = None, api_key: str | None = None
    ) -> dict[str, Any]:
        """
        Get full drug label by set ID.

        Args:
            set_id: Label set ID
            sections: Specific sections to retrieve (optional)
            api_key: Optional OpenFDA API key

        Returns:
            Dict with full label information
        """
        params = {
            "search": f'id:"{set_id}"',
            "limit": 1,
        }

        if api_key:
            params["api_key"] = api_key

        try:
            # Use full URL for OpenFDA endpoints
            response = await self._request("GET", url=OPENFDA_DRUG_LABELS_URL, params=params, return_json=False)
            response = json.loads(response)

            results = response.get("results", [])
            if not results:
                return self.format_response(
                    None, {"error": f"Drug label '{set_id}' not found"}
                )

            result = results[0]
            openfda = result.get("openfda", {})

            # Extract requested sections or all sections
            label_data = {
                "set_id": result.get("id"),
                "brand_name": openfda.get("brand_name", [None])[0]
                if openfda.get("brand_name")
                else None,
                "generic_name": openfda.get("generic_name", [None])[0]
                if openfda.get("generic_name")
                else None,
            }

            # Add sections
            if sections:
                for section in sections:
                    if section in result:
                        label_data[section] = result[section]
            else:
                # Include common sections
                common_sections = [
                    "indications_and_usage",
                    "dosage_and_administration",
                    "contraindications",
                    "warnings_and_precautions",
                    "adverse_reactions",
                    "drug_interactions",
                    "pregnancy",
                    "pediatric_use",
                    "geriatric_use",
                    "overdosage",
                ]
                for section in common_sections:
                    if section in result:
                        label_data[section] = result[section]

            return self.format_response(label_data)
        except Exception as e:
            logger.error(f"Failed to fetch drug label {set_id}: {e}", exc_info=True)
            return self.format_response(None, {"error": f"OpenFDA API error: {str(e)}"})

    async def search_device_events(
        self,
        device: str | None = None,
        manufacturer: str | None = None,
        problem: str | None = None,
        limit: int = OPENFDA_DEFAULT_LIMIT,
        page: int = 1,
        api_key: str | None = None,
    ) -> dict[str, Any]:
        """
        Search FDA device adverse event reports (MAUDE).

        Args:
            device: Device name to search for
            manufacturer: Manufacturer name
            problem: Device problem description
            limit: Maximum number of results per page
            page: Page number (1-based)
            api_key: Optional OpenFDA API key

        Returns:
            Dict with device event results
        """
        search_parts = []

        if device:
            device_sanitized = sanitize_input(device, max_length=100)
            if device_sanitized:
                search_parts.append(
                    f'(device.brand_name:"{device_sanitized}" OR '
                    f'device.generic_name:"{device_sanitized}" OR '
                    f'device.openfda.device_name:"{device_sanitized}")'
                )

        if manufacturer:
            manufacturer_sanitized = sanitize_input(manufacturer, max_length=100)
            if manufacturer_sanitized:
                search_parts.append(
                    f'device.manufacturer_d_name:"{manufacturer_sanitized}"'
                )

        if problem:
            problem_sanitized = sanitize_input(problem, max_length=200)
            if problem_sanitized:
                search_parts.append(f'mdr_text:"{problem_sanitized}"')

        if not search_parts:
            return self.format_response(
                [], {"error": "Please specify at least one search parameter"}
            )

        search_query = " AND ".join(search_parts)
        skip = (page - 1) * limit

        params = {
            "search": search_query,
            "limit": min(limit, OPENFDA_MAX_LIMIT),
            "skip": skip,
        }

        if api_key:
            params["api_key"] = api_key

        try:
            # Use full URL for OpenFDA endpoints
            response = await self._request("GET", url=OPENFDA_DEVICE_EVENTS_URL, params=params, return_json=False)
            response = json.loads(response)

            results = response.get("results", [])
            meta = response.get("meta", {})
            results_meta = meta.get("results", {})
            total = results_meta.get("total", len(results))

            # Format results
            formatted_results = []
            for result in results:
                device_info = (
                    result.get("device", [{}])[0] if result.get("device") else {}
                )
                formatted_results.append(
                    {
                        "mdr_report_key": result.get("mdr_report_key"),
                        "date_received": result.get("date_received"),
                        "device": {
                            "brand_name": device_info.get("brand_name"),
                            "generic_name": device_info.get("generic_name"),
                            "manufacturer": device_info.get("manufacturer_d_name"),
                        },
                        "event_type": result.get("event_type"),
                        "mdr_text": result.get("mdr_text", [None])[0]
                        if result.get("mdr_text")
                        else None,
                    }
                )

            return self.format_response(
                formatted_results,
                {
                    "total": total,
                    "page": page,
                    "page_size": limit,
                },
            )
        except Exception as e:
            logger.error(f"Device event search failed: {e}", exc_info=True)
            return self.format_response([], {"error": f"OpenFDA API error: {str(e)}"})
