"""
MyVariant.info API Client
Documentation: https://docs.myvariant.info/
Provides variant annotations and population frequency data
"""

import json
import logging
from typing import Any

from .base_client import BaseAPIClient

logger = logging.getLogger(__name__)

MYVARIANT_BASE_URL = "https://myvariant.info/v1"
MYVARIANT_QUERY_URL = f"{MYVARIANT_BASE_URL}/query"
MYVARIANT_GET_URL = f"{MYVARIANT_BASE_URL}/variant"


class MyVariantClient(BaseAPIClient):
    """Client for MyVariant.info API."""

    def __init__(self):
        """Initialize MyVariant client."""
        super().__init__(
            base_url=MYVARIANT_BASE_URL,
            api_name="MyVariant",
            timeout=60.0,
            rate_limit_delay=0.5,
        )

    async def search_variants(
        self,
        gene: str | None = None,
        hgvsp: str | None = None,
        hgvsc: str | None = None,
        rsid: str | None = None,
        significance: str | None = None,
        min_frequency: float | None = None,
        max_frequency: float | None = None,
        cadd_min: float | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Search variants using MyVariant.info query API.

        Args:
            gene: Gene symbol (e.g., 'BRAF', 'TP53')
            hgvsp: Protein change (e.g., 'p.V600E')
            hgvsc: Coding sequence change (e.g., 'c.1799T>A')
            rsid: dbSNP rsID (e.g., 'rs113488022')
            significance: Clinical significance filter ('pathogenic', 'likely_pathogenic', etc.)
            min_frequency: Minimum allele frequency
            max_frequency: Maximum allele frequency
            cadd_min: Minimum CADD score
            limit: Maximum number of results
            offset: Result offset for pagination

        Returns:
            Dict with variant search results
        """
        query_parts = []

        if gene:
            query_parts.append(f"dbnsfp.genename:{gene}")
        if hgvsp:
            query_parts.append(f'dbnsfp.hgvsp:"{hgvsp}"')
        if hgvsc:
            query_parts.append(f'dbnsfp.hgvsc:"{hgvsc}"')
        if rsid:
            query_parts.append(f'dbsnp.rsid:"{rsid}"')
        if significance:
            query_parts.append(f'clinvar.rcv.clinical_significance:"{significance}"')
        if min_frequency is not None:
            query_parts.append(f"gnomad_exome.af.af:>={min_frequency}")
        if max_frequency is not None:
            query_parts.append(f"gnomad_exome.af.af:<={max_frequency}")
        if cadd_min is not None:
            query_parts.append(f"cadd.phred:>={cadd_min}")

        if not query_parts:
            return self.format_response(
                [], {"error": "At least one search parameter is required"}
            )

        query = " AND ".join(query_parts)

        params = {
            "q": query,
            "size": limit,
            "from": offset,
            "fields": "all",
        }

        try:
            response = await self._request("GET", url=MYVARIANT_QUERY_URL, params=params, return_json=False)
            data = json.loads(response)

            hits = data.get("hits", [])
            total = data.get("total", len(hits))

            return self.format_response(
                hits,
                {
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                },
            )
        except Exception as e:
            logger.error(f"Variant search failed: {e}", exc_info=True)
            return self.format_response([], {"error": f"MyVariant API error: {str(e)}"})

    async def get_variant(
        self, variant_id: str, include_external: bool = False
    ) -> dict[str, Any]:
        """
        Get comprehensive variant details by ID.

        Args:
            variant_id: Variant ID (rsID, HGVS, or MyVariant ID like 'chr7:g.140753336A>T')
            include_external: Whether to include external annotations (TCGA, cBioPortal, OncoKB)

        Returns:
            Dict with full variant annotations
        """
        try:
            response = await self._request("GET", url=f"{MYVARIANT_GET_URL}/{variant_id}", params={"fields": "all"}, return_json=False)
            data = json.loads(response)

            # MyVariant returns hits array, get first hit
            if isinstance(data, dict) and "hits" in data:
                hits = data.get("hits", [])
                if hits:
                    variant_data = hits[0]
                else:
                    return self.format_response(
                        None, {"error": f"Variant '{variant_id}' not found"}
                    )
            elif isinstance(data, dict):
                variant_data = data
            else:
                return self.format_response(
                    None,
                    {"error": f"Unexpected response format for variant '{variant_id}'"},
                )

            # Note: External annotations (TCGA, cBioPortal, OncoKB) would require
            # additional API calls - simplified for now
            if include_external:
                variant_data["_external_annotations"] = (
                    "Available but not included in this implementation"
                )

            return self.format_response(variant_data)
        except Exception as e:
            logger.error(f"Failed to fetch variant {variant_id}: {e}", exc_info=True)
            return self.format_response(
                None, {"error": f"MyVariant API error: {str(e)}"}
            )
