"""
Reactome API Client
Documentation: https://reactome.org/dev/content-service
Base URL: https://reactome.org/ContentService
"""

from .base_client import BaseAPIClient


class ReactomeClient(BaseAPIClient):
    """Client for interacting with the Reactome Content Service API"""

    def __init__(self):
        super().__init__(
            base_url="https://reactome.org/ContentService",
            api_name="Reactome",
            timeout=30.0,
        )

    async def get_pathway(self, pathway_id: str) -> dict:
        """
        Get detailed information about a specific pathway

        Args:
            pathway_id: Reactome pathway stable identifier (e.g., 'R-HSA-1640170')
                       Note: KEGG pathway IDs (e.g., 'hsa04010') are not supported.
                       Use Reactome pathway IDs that start with 'R-HSA-', 'R-MMU-', etc.

        Returns:
            Dict with pathway information
        """
        # Validate pathway ID format
        if not pathway_id.startswith("R-"):
            raise Exception(
                f"Invalid pathway ID format: '{pathway_id}'. "
                "Reactome pathway IDs must start with 'R-' (e.g., 'R-HSA-1640170'). "
                "KEGG pathway IDs (e.g., 'hsa04010') are not supported by this endpoint."
            )

        # Reactome uses /data/query/{pathway_id} endpoint, not /data/pathway/{pathway_id}
        try:
            data = await self._get(f"/data/query/{pathway_id}")
            return self.format_response(data)
        except Exception as e:
            # If query endpoint fails, try the pathway endpoint as fallback
            if "404" in str(e) or "Not Found" in str(e):
                try:
                    data = await self._get(f"/data/pathway/{pathway_id}")
                    return self.format_response(data)
                except Exception:
                    raise Exception(
                        f"Pathway '{pathway_id}' not found. "
                        "Please verify the pathway ID is correct and exists in Reactome."
                    ) from e
            raise

    async def query_pathways(self, query: str, species: str = "Homo sapiens") -> dict:
        """
        Query pathways by keyword, gene, or protein name

        Args:
            query: Search query (pathway name, gene symbol, or protein name)
            species: Species filter (default: "Homo sapiens"). Can be species name or taxon ID (e.g., "9606" for human)

        Returns:
            Dict with matching pathways (includes metadata if results found)
        """
        # Reactome uses /search/query endpoint, not /query
        # Convert species name to taxon ID if needed
        if species == "Homo sapiens":
            species = "9606"
        params = {"query": query, "species": species}
        data = await self._get("/search/query", params=params)
        # Filter results to only pathways
        if isinstance(data, dict) and "results" in data:
            pathway_results = []
            for group in data.get("results", []):
                if group.get("typeName") == "Pathway":
                    pathway_results.extend(group.get("entries", []))
            formatted_data = {"pathways": pathway_results, "total": len(pathway_results)}
            return self.format_response(formatted_data, {"results": len(pathway_results)})
        return self.format_response(data)

    async def get_pathway_participants(self, pathway_id: str) -> dict | list:
        """
        Get all participants (genes, proteins, small molecules) in a pathway

        Args:
            pathway_id: Reactome pathway stable identifier (e.g., 'R-HSA-1640170')

        Returns:
            Dict or list with pathway participants (includes metadata if available)
        """
        # Validate pathway ID format
        if not pathway_id.startswith("R-"):
            raise Exception(
                f"Invalid pathway ID format: '{pathway_id}'. "
                "Reactome pathway IDs must start with 'R-' (e.g., 'R-HSA-1640170')."
            )

        # Try multiple endpoint patterns as Reactome API structure may vary
        endpoints_to_try = [
            f"/data/pathway/{pathway_id}/participatingMolecules",
            f"/data/query/{pathway_id}/participatingMolecules",
            f"/data/participatingMolecules/{pathway_id}",
        ]

        last_error = None
        for endpoint in endpoints_to_try:
            try:
                data = await self._get(endpoint)
                participant_count = len(data) if isinstance(data, list) else None
                metadata = {"participants": participant_count} if participant_count else None
                return self.format_response(data, metadata)
            except Exception as e:
                last_error = e
                # If it's not a 404, re-raise immediately
                if "404" not in str(e) and "Not Found" not in str(e):
                    raise
                # Otherwise, try next endpoint

        # If all endpoints failed, return pathway data with a note
        # that participants endpoint is not available, but include pathway info
        try:
            pathway_data = await self._get(f"/data/query/{pathway_id}")
            fallback_data = {
                "message": "Direct participants endpoint not available for this pathway. "
                "Pathway information retrieved instead. "
                "To get participants, query individual pathway events.",
                "pathway": pathway_data,
                "note": "Use query_pathways() to search for specific genes/proteins, "
                "or query individual pathway events to get their participants.",
            }
            return self.format_response(fallback_data)
        except Exception:
            # If we can't even get pathway data, raise the original error
            raise Exception(
                f"Pathway '{pathway_id}' not found or participants endpoint unavailable. "
                "Please verify the pathway ID is correct. "
                f"Original error: {str(last_error)}"
            ) from last_error

    async def get_disease_pathways(self, disease_name: str) -> dict | list:
        """
        Get pathways associated with a disease

        Args:
            disease_name: Disease name (e.g., 'multiple sclerosis')

        Returns:
            Dict or list with disease-associated pathways (includes metadata)
        """
        # First, search for the disease using the correct endpoint
        params = {"query": disease_name, "species": "9606"}
        search_results = await self._get("/search/query", params=params)

        # Filter for disease entities and get their pathways
        disease_pathways: list[dict] = []
        if isinstance(search_results, dict) and "results" in search_results:
            for group in search_results.get("results", []):
                for result in group.get("entries", []):
                    if (
                        result.get("type") == "Disease"
                        or result.get("exactType") == "Disease"
                    ):
                        disease_id = result.get("stId") or result.get("id")
                        if disease_id:
                            try:
                                # Get pathways for this disease
                                pathway_data = await self._get(
                                    f"/data/disease/{disease_id}/pathways"
                                )
                                if isinstance(pathway_data, list):
                                    disease_pathways.extend(pathway_data)
                            except Exception:
                                # If disease pathway endpoint doesn't exist, continue
                                pass

        if not disease_pathways:
            no_results_data = {
                "message": f"No pathways found for disease '{disease_name}'. Try searching for pathways directly.",
                "pathways": [],
            }
            return self.format_response(no_results_data, {"results": 0})

        return self.format_response(disease_pathways, {"pathways": len(disease_pathways)})
