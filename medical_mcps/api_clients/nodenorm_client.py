"""
Node Normalization API Client
Documentation: https://nodenormalization-sri.renci.org/1.5/openapi.json
Base URL: https://nodenormalization-sri.renci.org/1.5

Node Normalization takes a CURIE (Compact URI) and returns:
1. The preferred CURIE for this entity
2. All other known equivalent identifiers for the entity
3. Semantic types for the entity as defined by the BioLink Model

The data is created by Babel, which finds identifier equivalences and ensures
CURIE prefixes are BioLink Model Compliant.
"""

from .base_client import BaseAPIClient


class NodeNormClient(BaseAPIClient):
    """Client for interacting with the Node Normalization API"""

    def __init__(self):
        super().__init__(
            base_url="https://nodenormalization-sri.renci.org/1.5",
            api_name="Node Normalization",
            timeout=30.0,
        )

    async def get_semantic_types(self) -> dict | list | str:
        """
        Get all BioLink semantic types for which normalization has been attempted.
        This helps determine which entity types can be normalized.

        Returns:
            Dict with semantic types organized by category
        """
        data = await self._get("/get_semantic_types")
        return self.format_response(data)

    async def get_curie_prefixes(self) -> dict | list | str:
        """
        Get all CURIE prefixes available in the normalization database.
        This shows which prefixes are supported (e.g., DRUGBANK, MONDO, NCIT).
        Each prefix entry includes the number of times it's used for each semantic type.

        Returns:
            Dict with CURIE prefixes and their usage counts
        """
        data = await self._get("/get_curie_prefixes")
        return self.format_response(data)

    async def get_normalized_nodes(
        self,
        curies: list[str],
        conflate: bool = True,
        drug_chemical_conflate: bool = False,
        description: bool = False,
        individual_types: bool = False,
        include_taxa: bool = True,
    ) -> dict | list | str:
        """
        Get normalized identifiers and semantic types for one or more CURIEs.

        This is the core function: given a CURIE from any source (e.g., DRUGBANK:DB05266),
        it returns:
        - The preferred CURIE for this entity
        - All equivalent identifiers across databases
        - Semantic types from the BioLink Model

        Args:
            curies: List of CURIEs to normalize (e.g., ['DRUGBANK:DB05266', 'MONDO:0001134'])
            conflate: Whether to apply gene/protein conflation (default: True)
            drug_chemical_conflate: Whether to apply drug/chemical conflation (default: False)
            description: Whether to return CURIE descriptions when possible (default: False)
            individual_types: Whether to return individual types for equivalent identifiers (default: False)
            include_taxa: Whether to return taxa for equivalent identifiers (default: True)

        Returns:
            Dict with normalized node information (includes metadata)

        Example:
            Input: ['DRUGBANK:DB05266']
            Output: {
                'DRUGBANK:DB05266': {
                    'id': {'identifier': 'CHEBI:...', 'label': '...'},
                    'equivalent_identifiers': [...],
                    'type': ['biolink:Drug', 'biolink:ChemicalEntity']
                }
            }
        """
        # Use POST method for better handling of multiple CURIEs
        payload = {"curies": curies}
        result = await self._post("/get_normalized_nodes", json_data=payload)

        # Format the response with additional metadata
        formatted_result = {
            "input_curies": curies,
            "normalization_options": {
                "conflate": conflate,
                "drug_chemical_conflate": drug_chemical_conflate,
                "description": description,
                "individual_types": individual_types,
                "include_taxa": include_taxa,
            },
            "normalized_nodes": result,
        }

        metadata = {
            "input_count": len(curies),
            "normalized_count": len(result) if isinstance(result, dict) else None,
        }
        return self.format_response(formatted_result, metadata)

    async def get_allowed_conflations(self) -> dict | list | str:
        """
        Get the available conflation types that can be applied during normalization.
        Conflations merge equivalent entities (e.g., genes and proteins).

        Returns:
            Dict with available conflation types
        """
        data = await self._get("/get_allowed_conflations")
        return self.format_response(data)
