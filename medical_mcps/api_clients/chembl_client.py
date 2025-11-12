"""
ChEMBL API Client
Documentation: https://github.com/chembl/chembl_webresource_client
Uses: chembl_webresource_client library (synchronous, wrapped in async)
"""

import asyncio
import logging
from typing import Any

from chembl_webresource_client.new_client import new_client

from .base_client import BaseAPIClient

logger = logging.getLogger(__name__)


class ChEMBLClient(BaseAPIClient):
    """
    Client for interacting with ChEMBL database

    Note: ChEMBL webresource client is synchronous, so we wrap all calls
    in asyncio.to_thread() to make them async-compatible.
    """

    def __init__(self):
        """Initialize ChEMBL client"""
        super().__init__(
            base_url="",  # Not used - ChEMBL uses library, not HTTP
            api_name="ChEMBL",
            timeout=60.0,  # ChEMBL can be slow
            rate_limit_delay=0.5,  # Conservative rate limiting
        )
        self.chembl_client = new_client

    def format_response(
        self,
        data: dict[str, Any] | str | list | None,
        metadata: dict[str, Any] | None = None,
    ) -> dict:
        """
        Format response as structured dict with metadata.
        Overrides BaseAPIClient to use ChEMBL's structured format.

        Args:
            data: Response data (dict, list, str, or None)
            metadata: Optional metadata

        Returns:
            Dict with api_source, data, and optional metadata
        """
        response = {
            "api_source": self.api_name,
            "data": data,
        }
        if metadata:
            response["metadata"] = metadata
        return response

    async def _run_sync(self, func, *args, **kwargs):
        """Run synchronous function in thread pool"""
        return await asyncio.to_thread(func, *args, **kwargs)

    async def get_molecule(self, molecule_chembl_id: str) -> dict:
        """
        Get molecule information by ChEMBL ID

        Args:
            molecule_chembl_id: ChEMBL molecule ID (e.g., 'CHEMBL2108041')

        Returns:
            Dict with molecule data (includes api_source and optional metadata)
        """
        logger.info(f"Getting molecule: {molecule_chembl_id}")

        def _sync_query():
            molecules = self.chembl_client.molecule.filter(
                molecule_chembl_id=molecule_chembl_id
            ).only(
                [
                    "molecule_chembl_id",
                    "pref_name",
                    "molecule_type",
                    "max_phase",
                    "first_approval",
                    "molecular_weight",
                    "alogp",
                ]
            )
            result = list(molecules)
            return result[0] if result else None

        try:
            data = await self._run_sync(_sync_query)
            if data is None:
                return self.format_response(
                    None, {"error": f"Molecule {molecule_chembl_id} not found"}
                )
            return self.format_response(data)
        except Exception as e:
            logger.error(
                f"Error getting molecule {molecule_chembl_id}: {e}", exc_info=True
            )
            return self.format_response(None, {"error": f"ChEMBL API error: {str(e)}"})

    async def search_molecules(self, query: str, limit: int = 20) -> dict:
        """
        Search molecules by name or synonym

        Args:
            query: Search query (molecule name or synonym)
            limit: Maximum number of results (default: 20)

        Returns:
            JSON string with search results
        """
        logger.info(f"Searching molecules: {query}")

        def _sync_query():
            molecules = self.chembl_client.molecule.filter(
                molecule_synonyms__synonyms__icontains=query
            ).only(
                [
                    "molecule_chembl_id",
                    "pref_name",
                    "molecule_type",
                    "max_phase",
                ]
            )[:limit]
            return list(molecules)

        try:
            data = await self._run_sync(_sync_query)
            return self.format_response(data, {"query": query, "count": len(data)})
        except Exception as e:
            logger.error(f"Error searching molecules: {e}", exc_info=True)
            return self.format_response(None, {"error": f"ChEMBL API error: {str(e)}"})

    async def get_target(self, target_chembl_id: str) -> dict:
        """
        Get target information by ChEMBL ID

        Args:
            target_chembl_id: ChEMBL target ID (e.g., 'CHEMBL2058')

        Returns:
            Dict with target data (includes api_source and optional metadata)
        """
        logger.info(f"Getting target: {target_chembl_id}")

        def _sync_query():
            targets = self.chembl_client.target.filter(
                target_chembl_id=target_chembl_id
            ).only(
                [
                    "target_chembl_id",
                    "pref_name",
                    "target_type",
                    "organism",
                ]
            )
            result = list(targets)
            return result[0] if result else None

        try:
            data = await self._run_sync(_sync_query)
            if data is None:
                return self.format_response(
                    None, {"error": f"Target {target_chembl_id} not found"}
                )
            return self.format_response(data)
        except Exception as e:
            logger.error(f"Error getting target {target_chembl_id}: {e}", exc_info=True)
            return self.format_response(None, {"error": f"ChEMBL API error: {str(e)}"})

    async def search_targets(self, query: str, limit: int = 20) -> dict:
        """
        Search targets by name or synonym

        Args:
            query: Search query (target name or synonym)
            limit: Maximum number of results (default: 20)

        Returns:
            JSON string with search results
        """
        logger.info(f"Searching targets: {query}")

        def _sync_query():
            targets = self.chembl_client.target.filter(
                target_synonyms__synonyms__icontains=query
            ).only(
                [
                    "target_chembl_id",
                    "pref_name",
                    "target_type",
                    "organism",
                ]
            )[:limit]
            return list(targets)

        try:
            data = await self._run_sync(_sync_query)
            return self.format_response(data, {"query": query, "count": len(data)})
        except Exception as e:
            logger.error(f"Error searching targets: {e}", exc_info=True)
            return self.format_response(None, {"error": f"ChEMBL API error: {str(e)}"})

    async def get_activities(
        self,
        target_chembl_id: str | None = None,
        molecule_chembl_id: str | None = None,
        limit: int = 50,
    ) -> dict:
        """
        Get bioactivity data

        Args:
            target_chembl_id: Filter by target (optional)
            molecule_chembl_id: Filter by molecule (optional)
            limit: Maximum number of results (default: 50)

        Returns:
            Dict with activity data (includes api_source and metadata)
        """
        logger.info(
            f"Getting activities: target={target_chembl_id}, molecule={molecule_chembl_id}"
        )

        def _sync_query():
            activities = self.chembl_client.activity
            if target_chembl_id:
                activities = activities.filter(target_chembl_id=target_chembl_id)
            if molecule_chembl_id:
                activities = activities.filter(molecule_chembl_id=molecule_chembl_id)
            activities = activities.only(
                [
                    "activity_id",
                    "molecule_chembl_id",
                    "target_chembl_id",
                    "standard_value",
                    "standard_type",
                    "standard_units",
                    "assay_chembl_id",
                ]
            )[:limit]
            return list(activities)

        try:
            data = await self._run_sync(_sync_query)
            return self.format_response(
                data,
                {
                    "target_chembl_id": target_chembl_id,
                    "molecule_chembl_id": molecule_chembl_id,
                    "count": len(data),
                },
            )
        except Exception as e:
            logger.error(f"Error getting activities: {e}", exc_info=True)
            return self.format_response(None, {"error": f"ChEMBL API error: {str(e)}"})

    async def get_mechanism(self, molecule_chembl_id: str) -> dict:
        """
        Get mechanism of action for a molecule

        Args:
            molecule_chembl_id: ChEMBL molecule ID

        Returns:
            Dict with mechanism data (includes api_source and metadata)
        """
        logger.info(f"Getting mechanism for molecule: {molecule_chembl_id}")

        def _sync_query():
            mechanisms = self.chembl_client.mechanism.filter(
                molecule_chembl_id=molecule_chembl_id
            ).only(
                [
                    "mechanism_id",
                    "molecule_chembl_id",
                    "target_chembl_id",
                    "mechanism_of_action",
                    "action_type",
                ]
            )
            return list(mechanisms)

        try:
            data = await self._run_sync(_sync_query)
            return self.format_response(
                data,
                {"molecule_chembl_id": molecule_chembl_id, "count": len(data)},
            )
        except Exception as e:
            logger.error(f"Error getting mechanism: {e}", exc_info=True)
            return self.format_response(None, {"error": f"ChEMBL API error: {str(e)}"})

    async def find_drugs_by_target(self, target_chembl_id: str, limit: int = 50) -> dict:
        """
        Find all drugs/compounds targeting a specific protein

        Args:
            target_chembl_id: ChEMBL target ID
            limit: Maximum number of results (default: 50)

        Returns:
            Dict with molecules and their activities (includes api_source and metadata)
        """
        logger.info(f"Finding drugs for target: {target_chembl_id}")

        def _sync_query():
            # Get activities for this target
            activities = self.chembl_client.activity.filter(
                target_chembl_id=target_chembl_id
            ).only(["molecule_chembl_id", "standard_value", "standard_type"])[:limit]
            activity_list = list(activities)

            # Get unique molecule IDs
            mol_ids = list(
                set(
                    [
                        a["molecule_chembl_id"]
                        for a in activity_list
                        if a.get("molecule_chembl_id")
                    ]
                )
            )[:limit]

            # Get molecule details
            if not mol_ids:
                return []
            molecules = self.chembl_client.molecule.filter(
                molecule_chembl_id__in=mol_ids
            ).only(
                [
                    "molecule_chembl_id",
                    "pref_name",
                    "molecule_type",
                    "max_phase",
                ]
            )
            return list(molecules)

        try:
            data = await self._run_sync(_sync_query)
            return self.format_response(
                data,
                {"target_chembl_id": target_chembl_id, "count": len(data)},
            )
        except Exception as e:
            logger.error(f"Error finding drugs by target: {e}", exc_info=True)
            return self.format_response(None, {"error": f"ChEMBL API error: {str(e)}"})

    async def find_drugs_by_indication(
        self, disease_query: str, limit: int = 50
    ) -> dict:
        """
        Find all drugs for a disease/indication

        Args:
            disease_query: Disease name or MeSH heading (e.g., 'Multiple Sclerosis')
            limit: Maximum number of results (default: 50)

        Returns:
            Dict with drug-indication pairs (includes api_source and metadata)
        """
        logger.info(f"Finding drugs for indication: {disease_query}")

        def _sync_query():
            indications = self.chembl_client.drug_indication.filter(
                mesh_heading__icontains=disease_query
            ).only(["drug_chembl_id", "mesh_heading", "mesh_id"])[:limit]
            return list(indications)

        try:
            data = await self._run_sync(_sync_query)
            return self.format_response(
                data, {"disease_query": disease_query, "count": len(data)}
            )
        except Exception as e:
            logger.error(f"Error finding drugs by indication: {e}", exc_info=True)
            return self.format_response(None, {"error": f"ChEMBL API error: {str(e)}"})

    async def get_drug_indications(self, molecule_chembl_id: str) -> dict:
        """
        Get all indications for a specific drug

        Args:
            molecule_chembl_id: ChEMBL molecule ID

        Returns:
            Dict with indication data (includes api_source and metadata)
        """
        logger.info(f"Getting indications for molecule: {molecule_chembl_id}")

        def _sync_query():
            # First get drug_chembl_id from molecule
            molecules = self.chembl_client.molecule.filter(
                molecule_chembl_id=molecule_chembl_id
            ).only(["drug_chembl_id"])
            mol_list = list(molecules)
            if not mol_list or not mol_list[0].get("drug_chembl_id"):
                return []

            drug_id = mol_list[0]["drug_chembl_id"]
            indications = self.chembl_client.drug_indication.filter(
                drug_chembl_id=drug_id
            ).only(["drug_chembl_id", "mesh_heading", "mesh_id"])
            return list(indications)

        try:
            data = await self._run_sync(_sync_query)
            return self.format_response(
                data,
                {"molecule_chembl_id": molecule_chembl_id, "count": len(data)},
            )
        except Exception as e:
            logger.error(f"Error getting drug indications: {e}", exc_info=True)
            return self.format_response(None, {"error": f"ChEMBL API error: {str(e)}"})
