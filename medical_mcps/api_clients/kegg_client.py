"""
KEGG API Client
Documentation: https://www.kegg.jp/kegg/rest/keggapi.html
Base URL: https://rest.kegg.jp
Rate Limits: Must be respected - use delays between requests
"""

from .base_client import BaseAPIClient


class KEGGClient(BaseAPIClient):
    """Client for interacting with the KEGG REST API"""

    def __init__(self):
        # KEGG recommends delays between requests - 0.5s minimum
        super().__init__(
            base_url="https://rest.kegg.jp",
            api_name="KEGG",
            timeout=30.0,
            rate_limit_delay=0.5,
        )

    async def get_pathway(self, pathway_id: str) -> str:
        """
        Get pathway information by KEGG pathway ID

        Args:
            pathway_id: KEGG pathway ID (e.g., 'hsa04010', 'map00010')

        Returns:
            Pathway data in KEGG flat file format
        """
        data = await self._request("GET", endpoint=f"/get/{pathway_id}", return_json=False)
        return self.format_response(data)

    async def list_pathways(self, organism: str | None = None) -> str:
        """
        List pathways. If organism is provided, lists organism-specific pathways.

        Args:
            organism: KEGG organism code (e.g., 'hsa' for human). If None, lists reference pathways.

        Returns:
            List of pathways with IDs and names
        """
        if organism:
            data = await self._request("GET", endpoint=f"/list/pathway/{organism}", return_json=False)
        else:
            data = await self._request("GET", endpoint="/list/pathway", return_json=False)

        # Return text directly (no metadata for simplicity)
        return self.format_response(data)

    async def find_pathways(self, query: str) -> str:
        """
        Find pathways matching a query keyword

        Args:
            query: Search keyword

        Returns:
            Matching pathways
        """
        data = await self._request("GET", endpoint=f"/find/pathway/{query}", return_json=False)

        # Check for no results
        if not data.strip() or data.strip() == "":
            return self.format_response(
                f"No pathways found matching '{query}'. Try a different search term."
            )

        return self.format_response(data)

    async def get_gene(self, gene_id: str) -> str:
        """
        Get gene information by KEGG gene ID

        Args:
            gene_id: KEGG gene ID (e.g., 'hsa:10458')

        Returns:
            Gene data in KEGG flat file format
        """
        data = await self._request("GET", endpoint=f"/get/{gene_id}", return_json=False)
        return self.format_response(data)

    async def find_genes(self, query: str, organism: str | None = None) -> str:
        """
        Find genes matching a query keyword

        Args:
            query: Search keyword
            organism: KEGG organism code (e.g., 'hsa' for human). Optional.

        Returns:
            Matching genes
        """
        if organism:
            data = await self._request("GET", endpoint=f"/find/{organism}/{query}", return_json=False)
        else:
            data = await self._request("GET", endpoint=f"/find/genes/{query}", return_json=False)

        # Check for no results
        if not data.strip():
            return self.format_response(
                f"No genes found matching '{query}'. Try a different search term."
            )

        return self.format_response(data)

    async def get_disease(self, disease_id: str) -> str:
        """
        Get disease information by KEGG disease ID

        Args:
            disease_id: KEGG disease ID (e.g., 'H00001')

        Returns:
            Disease data in KEGG flat file format
        """
        data = await self._request("GET", endpoint=f"/get/{disease_id}", return_json=False)
        return self.format_response(data)

    async def find_diseases(self, query: str) -> str:
        """
        Find diseases matching a query keyword

        Args:
            query: Search keyword

        Returns:
            Matching diseases
        """
        data = await self._request("GET", endpoint=f"/find/disease/{query}", return_json=False)

        # Check for no results
        if not data.strip():
            return self.format_response(
                f"No diseases found matching '{query}'. Try a different search term."
            )

        return self.format_response(data)

    async def link_pathway_genes(self, pathway_id: str) -> str:
        """
        Get genes linked to a pathway

        Args:
            pathway_id: KEGG pathway ID (e.g., 'hsa04658', 'hsa:04658', 'map00010')

        Returns:
            List of genes linked to the pathway
        """
        # According to KEGG API docs: /link/hsa/hsa00010 returns human genes in pathway hsa00010
        # Format: /link/<target_db>/<source_db> where both are database entries

        # Handle different input formats
        if ":" in pathway_id:
            # Format: 'hsa:04658' -> extract organism and pathway
            parts = pathway_id.split(":")
            organism = parts[0]
            pathway_num = parts[1]
            # Reconstruct pathway ID: hsa04658
            pathway_id = f"{organism}{pathway_num}"

        # Extract organism from pathway ID (e.g., 'hsa04658' -> 'hsa', 'map00010' -> 'map')
        # KEGG pathway format: <org><5digits> or map<5digits>
        # Organism codes are typically 3 letters, sometimes 4
        if pathway_id.startswith("map"):
            # Reference pathway - use 'genes' as target (finds all organisms with this pathway)
            data = await self._request("GET", endpoint=f"/link/genes/{pathway_id}", return_json=False)
        elif len(pathway_id) >= 8:
            # Organism-specific pathway (e.g., 'hsa04658', 'mmu00010')
            # Try 3-letter org code first (most common)
            if pathway_id[3:8].isdigit():
                organism = pathway_id[:3]
                data = await self._request("GET", endpoint=f"/link/{organism}/{pathway_id}", return_json=False)
            # Try 4-letter org code if 3 doesn't work
            elif len(pathway_id) >= 9 and pathway_id[4:9].isdigit():
                organism = pathway_id[:4]
                data = await self._request("GET", endpoint=f"/link/{organism}/{pathway_id}", return_json=False)
            else:
                # Fallback: try with 'genes' target
                data = await self._request("GET", endpoint=f"/link/genes/{pathway_id}", return_json=False)
        else:
            # Try as-is, might be a valid format we don't recognize
            data = await self._request("GET", endpoint=f"/link/genes/{pathway_id}", return_json=False)

        # Check for no results
        if not data.strip():
            return self.format_response(
                f"No genes found linked to pathway '{pathway_id}'."
            )

        return self.format_response(data)
