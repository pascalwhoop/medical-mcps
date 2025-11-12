"""
UniProt API Client
Documentation: https://www.uniprot.org/help/api
Base URL: https://rest.uniprot.org
"""

import asyncio
import json

from .base_client import BaseAPIClient


class UniProtClient(BaseAPIClient):
    """Client for interacting with the UniProt REST API"""

    def __init__(self):
        super().__init__(
            base_url="https://rest.uniprot.org",
            api_name="UniProt",
            timeout=30.0,
        )

    async def get_protein(self, accession: str, format: str = "json") -> dict | str:
        """
        Get protein information by UniProt accession

        Args:
            accession: UniProt accession (e.g., 'P00520')
            format: Response format ('json', 'fasta', 'xml', etc.)

        Returns:
            Dict for JSON format, str for text formats (fasta, xml, etc.)
        """
        if format == "json":
            data = await self._get(f"/uniprotkb/{accession}")
            return self.format_response(data)
        else:
            url = f"{self.base_url}/uniprotkb/{accession}.{format}"
            text = await self._get_text_direct(url)
            return self.format_response(text)

    async def search_proteins(
        self, query: str, format: str = "json", limit: int = 25, offset: int = 0
    ) -> dict | str:
        """
        Search proteins in UniProtKB

        Args:
            query: Search query (e.g., 'gene:BRCA1 AND organism_id:9606')
            format: Response format ('json', 'tsv', 'fasta', etc.)
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            Dict for JSON format (includes metadata), str for text formats
        """
        params = {"query": query, "size": limit, "from": offset}
        if format == "json":
            data = await self._get("/uniprotkb/search", params=params)
            result_count = (
                len(data.get("results", [])) if isinstance(data, dict) else None
            )
            metadata = {"results": result_count} if result_count is not None else None
            return self.format_response(data, metadata)
        else:
            url = f"{self.base_url}/uniprotkb/search"
            params["format"] = format
            text = await self._get_text_direct(url, params=params)
            return self.format_response(text)

    async def get_protein_sequence(self, accession: str) -> str:
        """
        Get protein sequence in FASTA format

        Args:
            accession: UniProt accession

        Returns:
            FASTA sequence as string
        """
        url = f"{self.base_url}/uniprotkb/{accession}.fasta"
        text = await self._get_text_direct(url)
        return self.format_response(text)

    async def get_disease_associations(self, accession: str) -> dict:
        """
        Get disease associations for a protein

        Args:
            accession: UniProt accession

        Returns:
            Dict with disease associations (includes metadata)
        """
        data = await self._get(f"/uniprotkb/{accession}")
        # Extract disease information from the response
        diseases = []
        if "comments" in data:
            for comment in data["comments"]:
                if comment.get("commentType") == "DISEASE":
                    diseases.append(comment)

        # Format as dict for consistent response structure
        diseases_data = {"diseases": diseases, "count": len(diseases)}
        metadata = {"diseases": len(diseases)}
        return self.format_response(diseases_data, metadata)

    async def map_ids(self, from_db: str, to_db: str, ids: list[str]) -> dict | str:
        """
        Map identifiers between databases using UniProt ID mapping

        Args:
            from_db: Source database. Common values: 'UniProtKB_AC-ID', 'Gene_Name', 'Gene_Synonym', 'P_ENTREZGENEID'
            to_db: Target database. Common values: 'UniProtKB', 'Ensembl', 'GeneID', 'RefSeq_Protein'
            ids: List of identifiers to map

        Returns:
            Dict with mapping results (includes metadata) or str for errors/text responses
        """
        # UniProt ID mapping requires form-data, not JSON
        payload = {"from": from_db, "to": to_db, "ids": ",".join(ids)}
        response = await self._post("/idmapping/run", form_data=payload)

        # Check if there's an error in the response
        if "jobId" not in response:
            error_msg = (
                response.get("messages", [{}])[0].get("text", "Unknown error")
                if response.get("messages")
                else "Unknown error"
            )
            raise Exception(f"UniProt ID mapping error: {error_msg}")

        job_id = response.get("jobId")

        # Poll for results
        result_url = f"{self.base_url}/idmapping/status/{job_id}"
        for _ in range(30):  # Max 30 attempts
            await asyncio.sleep(1)
            status_text = await self._get_text_direct(result_url)
            status = json.loads(status_text)

            if status.get("results") or status.get("failedIds"):
                # Get results
                results_url = f"{self.base_url}/idmapping/stream/{job_id}"
                results_text = await self._get_text_direct(results_url)

                # Parse and count mappings
                try:
                    results_data = json.loads(results_text)
                    mapping_count = (
                        len(results_data.get("results", []))
                        if isinstance(results_data, dict)
                        else None
                    )
                    metadata = (
                        {"mappings": mapping_count}
                        if mapping_count is not None
                        else None
                    )
                    return self.format_response(results_data, metadata)
                except json.JSONDecodeError:
                    return self.format_response(results_text)

        return self.format_response("Error: Mapping job timed out after 30 seconds")
