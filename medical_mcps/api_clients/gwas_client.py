"""
GWAS Catalog API Client
Documentation: https://www.ebi.ac.uk/gwas/docs/api
Base URL: https://www.ebi.ac.uk/gwas/rest/api
"""

from .base_client import BaseAPIClient


class GWASClient(BaseAPIClient):
    """Client for interacting with the GWAS Catalog REST API"""

    def __init__(self):
        super().__init__(
            base_url="https://www.ebi.ac.uk/gwas/rest/api",
            api_name="GWAS Catalog",
            timeout=30.0,
        )

    async def get_association(self, association_id: str) -> dict:
        """
        Get association information by ID

        Args:
            association_id: GWAS association ID

        Returns:
            Dict with association data
        """
        data = await self._get(f"/associations/{association_id}")
        return self.format_response(data)

    async def search_associations(
        self,
        query: str | None = None,
        variant_id: str | None = None,
        study_id: str | None = None,
        trait: str | None = None,
        size: int = 20,
        page: int = 0,
    ) -> dict:
        """
        Search for associations

        Args:
            query: General search query
            variant_id: Variant ID (e.g., 'rs3093017')
            study_id: Study ID (e.g., 'GCST90132222')
            trait: Trait name
            size: Number of results per page
            page: Page number (0-indexed)

        Returns:
            Dict with search results (includes metadata)
        """
        params: dict = {"size": size, "page": page}
        if query:
            params["q"] = query
        if variant_id:
            params["variantId"] = variant_id
        if study_id:
            params["studyId"] = study_id
        if trait:
            params["efoTraits"] = trait

        data = await self._get("/associations", params=params)

        # Extract result count if available
        result_count = None
        if isinstance(data, dict) and "_embedded" in data:
            associations = data["_embedded"].get("associations", [])
            result_count = len(associations)

        metadata = (
            {"results": result_count, "page": page}
            if result_count is not None
            else {"page": page}
        )
        return self.format_response(data, metadata)

    async def get_variant(self, variant_id: str) -> dict:
        """
        Get variant information by ID

        Args:
            variant_id: Variant ID (e.g., 'rs3093017')

        Returns:
            Dict with variant data
        """
        data = await self._get(f"/singleNucleotidePolymorphisms/{variant_id}")
        return self.format_response(data)

    async def search_variants(
        self, query: str | None = None, size: int = 20, page: int = 0
    ) -> dict:
        """
        Search for variants

        Args:
            query: Search query (rsId like 'rs3093017')
            size: Number of results per page
            page: Page number (0-indexed)

        Returns:
            Dict with search results (includes metadata)
        """
        params: dict = {"size": size, "page": page}
        if query:
            params["rsId"] = query

        data = await self._get("/singleNucleotidePolymorphisms", params=params)

        # Extract result count if available
        result_count = None
        if isinstance(data, dict) and "_embedded" in data:
            snps = data["_embedded"].get("singleNucleotidePolymorphisms", [])
            result_count = len(snps)

        metadata = (
            {"results": result_count, "page": page}
            if result_count is not None
            else {"page": page}
        )
        return self.format_response(data, metadata)

    async def get_study(self, study_id: str) -> dict:
        """
        Get study information by ID

        Args:
            study_id: Study ID (e.g., 'GCST90132222')

        Returns:
            Dict with study data
        """
        data = await self._get(f"/studies/{study_id}")
        return self.format_response(data)

    async def search_studies(
        self,
        query: str | None = None,
        trait: str | None = None,
        size: int = 20,
        page: int = 0,
    ) -> dict:
        """
        Search for studies

        Args:
            query: Search query
            trait: Trait name
            size: Number of results per page
            page: Page number (0-indexed)

        Returns:
            Dict with search results (includes metadata)
        """
        params: dict = {"size": size, "page": page}
        if query:
            params["q"] = query
        if trait:
            params["efoTraits"] = trait

        data = await self._get("/studies", params=params)
        return self.format_response(data, {"page": page})

    async def get_trait(self, trait_id: str) -> dict:
        """
        Get trait information by ID

        Args:
            trait_id: EFO trait ID

        Returns:
            Dict with trait data
        """
        data = await self._get(f"/efoTraits/{trait_id}")
        return self.format_response(data)

    async def search_traits(
        self, query: str | None = None, size: int = 20, page: int = 0
    ) -> dict:
        """
        Search for traits

        Args:
            query: Search query (trait name)
            size: Number of results per page
            page: Page number (0-indexed)

        Returns:
            Dict with search results (includes metadata)
        """
        params: dict = {"size": size, "page": page}
        if query:
            params["q"] = query

        data = await self._get("/efoTraits", params=params)
        return self.format_response(data, {"page": page})
