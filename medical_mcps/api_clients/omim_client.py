"""
OMIM API Client
Documentation: https://omim.org/help/api
Base URL: https://api.omim.org/api
Authentication: API key required (provided by MCP client per-request, not stored on server)
"""

from .base_client import BaseAPIClient


class OMIMClient(BaseAPIClient):
    """Client for interacting with the OMIM API"""

    def __init__(self, api_key: str):
        """
        Initialize OMIM client with API key.
        
        Args:
            api_key: OMIM API key (required)
        
        Raises:
            ValueError: If api_key is None or empty
        """
        if not api_key:
            raise ValueError("OMIM API key is required")
        self.api_key = api_key
        super().__init__(
            base_url="https://api.omim.org/api",
            api_name="OMIM",
            timeout=30.0,
        )

    async def _get_omim(self, endpoint: str, params: dict | None = None) -> dict:
        """Make a GET request to the OMIM API with API key"""
        if params is None:
            params = {}
        params["apiKey"] = self.api_key
        params["format"] = "json"  # Always request JSON format
        return await self._get(endpoint, params)

    async def get_entry(self, mim_number: str, include: str = "text") -> dict:
        """
        Get entry information by MIM number
        
        Args:
            mim_number: MIM number (e.g., '104300')
            include: Fields to include ('text', 'allelicVariantList', 'geneMap', etc.)
        
        Returns:
            Dict with entry data
        """
        params = {"mimNumber": mim_number, "include": include}
        data = await self._get_omim("/entry", params=params)
        return self.format_response(data)

    async def search_entries(
        self,
        search: str,
        include: str = "text",
        limit: int = 20,
        start: int = 0
    ) -> dict:
        """
        Search entries
        
        Args:
            search: Search query
            include: Fields to include
            limit: Maximum number of results
            start: Starting index for pagination
        
        Returns:
            Dict with search results (includes metadata)
        """
        params = {
            "search": search,
            "include": include,
            "limit": limit,
            "start": start
        }
        data = await self._get_omim("/entry/search", params=params)
        return self.format_response(data, {"limit": limit, "start": start})

    async def get_gene(self, gene_symbol: str, include: str = "geneMap") -> dict:
        """
        Get gene information by gene symbol
        
        Args:
            gene_symbol: Gene symbol (e.g., 'BRCA1')
            include: Fields to include
        
        Returns:
            Dict with gene data
        """
        params = {"geneSymbol": gene_symbol, "include": include}
        data = await self._get_omim("/gene", params=params)
        return self.format_response(data)

    async def search_genes(
        self,
        search: str,
        include: str = "geneMap",
        limit: int = 20,
        start: int = 0
    ) -> dict:
        """
        Search genes
        
        Args:
            search: Search query
            include: Fields to include
            limit: Maximum number of results
            start: Starting index for pagination
        
        Returns:
            Dict with search results (includes metadata)
        """
        params = {
            "search": search,
            "include": include,
            "limit": limit,
            "start": start
        }
        data = await self._get_omim("/gene/search", params=params)
        return self.format_response(data, {"limit": limit, "start": start})

    async def get_phenotype(self, mim_number: str, include: str = "text") -> dict:
        """
        Get phenotype information by MIM number
        
        Args:
            mim_number: MIM number
            include: Fields to include
        
        Returns:
            Dict with phenotype data
        """
        params = {"mimNumber": mim_number, "include": include}
        data = await self._get_omim("/phenotypeMap", params=params)
        return self.format_response(data)

    async def search_phenotypes(
        self,
        search: str,
        include: str = "text",
        limit: int = 20,
        start: int = 0
    ) -> dict:
        """
        Search phenotypes
        
        Args:
            search: Search query
            include: Fields to include
            limit: Maximum number of results
            start: Starting index for pagination
        
        Returns:
            Dict with search results (includes metadata)
        """
        params = {
            "search": search,
            "include": include,
            "limit": limit,
            "start": start
        }
        data = await self._get_omim("/phenotypeMap/search", params=params)
        return self.format_response(data, {"limit": limit, "start": start})

