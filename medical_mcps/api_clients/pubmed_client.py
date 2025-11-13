"""
PubMed/PubTator3 API Client
Documentation: https://www.ncbi.nlm.nih.gov/research/pubtator3/api
Uses PubTator3 API for article search and Europe PMC for preprints
"""

import asyncio
import json
import logging
import re
from typing import Any

from pydantic import BaseModel, Field

from .base_client import BaseAPIClient

logger = logging.getLogger(__name__)

# PubTator3 API endpoints
PUBTATOR3_BASE_URL = "https://www.ncbi.nlm.nih.gov/research/pubtator3-api"
PUBTATOR3_SEARCH_URL = f"{PUBTATOR3_BASE_URL}/search/"
PUBTATOR3_FULLTEXT_URL = f"{PUBTATOR3_BASE_URL}/publications/export/biocjson"
PUBTATOR3_AUTOCOMPLETE_URL = f"{PUBTATOR3_BASE_URL}/entity/autocomplete/"

# Europe PMC API endpoints
EUROPE_PMC_BASE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest"


class EntityRequest(BaseModel):
    """Request for entity autocomplete."""

    concept: str | None = None  # "gene", "disease", "chemical", "variant"
    query: str
    limit: int = 1


class Entity(BaseModel):
    """Entity from autocomplete."""

    entity_id: str = Field(alias="_id")
    concept: str = Field(alias="biotype")
    name: str
    match: str | None = None


class PubTatorSearchRequest(BaseModel):
    """Request for PubTator3 search."""

    text: str
    size: int = 50


class PubTatorSearchResult(BaseModel):
    """Individual search result from PubTator3."""

    pmid: int | None = None
    pmcid: str | None = None
    title: str | None = None
    journal: str | None = None
    authors: list[str] | None = None
    date: str | None = None
    doi: str | None = None
    abstract: str | None = None


class PubTatorSearchResponse(BaseModel):
    """Search response from PubTator3."""

    results: list[PubTatorSearchResult] = Field(default_factory=list)
    page_size: int = 50
    current: int = 1
    count: int = 0
    total_pages: int = 1


class PubTatorArticle(BaseModel):
    """Full article from PubTator3."""

    pmid: int | None = None
    pmcid: str | None = None
    date: str | None = None
    journal: str | None = None
    authors: list[str] | None = None
    passages: list[dict[str, Any]] = Field(default_factory=list)

    @property
    def title(self) -> str:
        """Extract title from passages."""
        for passage in self.passages:
            infons = passage.get("infons", {})
            if infons.get("section_type") == "TITLE" or infons.get("type") == "title":
                return passage.get("text", "")
        return f"Article: {self.pmid}"

    @property
    def abstract(self) -> str:
        """Extract abstract from passages."""
        abstracts = []
        for passage in self.passages:
            infons = passage.get("infons", {})
            if (
                infons.get("section_type") == "ABSTRACT"
                or infons.get("type") == "abstract"
            ):
                abstracts.append(passage.get("text", ""))
        return "\n\n".join(abstracts)

    @property
    def full_text(self) -> str:
        """Extract full text from passages."""
        texts = []
        for passage in self.passages:
            infons = passage.get("infons", {})
            section_type = infons.get("section_type", "").upper()
            if section_type in {"INTRO", "RESULTS", "METHODS", "DISCUSS", "CONCL"}:
                texts.append(passage.get("text", ""))
        return "\n\n".join(texts)


class PubTatorFetchResponse(BaseModel):
    """Fetch response from PubTator3."""

    PubTator3: list[PubTatorArticle] = Field(default_factory=list, alias="PubTator3")

    @property
    def articles(self) -> list[PubTatorArticle]:
        """Get articles list."""
        return self.PubTator3


class EuropePMCResult(BaseModel):
    """Result from Europe PMC."""

    id: str | None = None
    source: str | None = None
    title: str | None = None
    authorString: str | None = None
    journalTitle: str | None = None
    pubYear: str | None = None
    doi: str | None = None
    abstractText: str | None = None
    publicationState: str | None = None


class EuropePMCResponse(BaseModel):
    """Response from Europe PMC."""

    resultList: dict[str, Any] = Field(default_factory=dict)

    @property
    def results(self) -> list[EuropePMCResult]:
        """Get results list."""
        return [EuropePMCResult(**r) for r in self.resultList.get("result", [])]

    @property
    def total(self) -> int:
        """Get total count."""
        return self.resultList.get("hitCount", 0)


class PubMedClient(BaseAPIClient):
    """Client for PubMed/PubTator3 API."""

    def __init__(self):
        """Initialize PubMed client."""
        super().__init__(
            base_url=PUBTATOR3_BASE_URL,
            api_name="PubMed",
            timeout=60.0,
            rate_limit_delay=0.5,  # Conservative rate limiting
        )

    async def autocomplete_entity(self, concept: str, query: str) -> Entity | None:
        """
        Autocomplete entity (gene, disease, chemical, variant).

        Args:
            concept: Entity type ("gene", "disease", "chemical", "variant")
            query: Query string

        Returns:
            Entity object or None if not found
        """
        try:
            params = {
                "concept": concept,
                "query": query,
                "limit": 1,
            }
            # Use full URL for autocomplete endpoint
            response = await self._request("GET", url=PUBTATOR3_AUTOCOMPLETE_URL, params=params, return_json=False)

            data = json.loads(response)
            if isinstance(data, list) and len(data) > 0:
                entity_data = data[0]
                return Entity(**entity_data)
            return None
        except Exception as e:
            logger.warning(f"Autocomplete failed for {concept}={query}: {e}")
            return None

    async def search_articles(
        self,
        genes: list[str] | None = None,
        diseases: list[str] | None = None,
        chemicals: list[str] | None = None,
        keywords: list[str] | None = None,
        variants: list[str] | None = None,
        limit: int = 50,
        page: int = 1,
    ) -> dict[str, Any]:
        """
        Search articles using PubTator3 API.

        Args:
            genes: List of gene names
            diseases: List of disease names
            chemicals: List of chemical/drug names
            keywords: List of keywords
            variants: List of variant names
            limit: Results per page
            page: Page number (1-based)

        Returns:
            Dict with search results
        """
        # Build query parts
        query_parts = []

        # Process keywords (support OR with |)
        if keywords:
            for keyword in keywords:
                if "|" in keyword:
                    or_terms = [term.strip() for term in keyword.split("|")]
                    or_query = "(" + " OR ".join(or_terms) + ")"
                    query_parts.append(or_query)
                else:
                    query_parts.append(keyword)

        # Process entities with autocomplete
        entity_tasks = []
        entity_values = []

        concepts = [
            ("gene", genes or []),
            ("disease", diseases or []),
            ("chemical", chemicals or []),
            ("variant", variants or []),
        ]

        for concept, values in concepts:
            for value in values:
                task = self.autocomplete_entity(concept, value)
                entity_tasks.append(task)
                entity_values.append((concept, value))

        # Execute autocomplete in parallel
        if entity_tasks:
            entities = await asyncio.gather(*entity_tasks)
            for (concept, value), entity in zip(entity_values, entities):
                if entity:
                    query_parts.append(entity.entity_id)
                else:
                    query_parts.append(value)

        # Build final query
        query_text = " AND ".join(query_parts) if query_parts else ""

        if not query_text:
            return self.format_response(
                [], {"error": "At least one search parameter is required"}
            )

        # Calculate pagination
        total_needed = page * limit
        params = {"text": query_text, "size": total_needed}

        try:
            # Make GET request to PubTator3 search API (API accepts GET with query params)
            # Use _get_text_direct since we're using a full URL, not a relative endpoint
            response_text = await self._request("GET", url=PUBTATOR3_SEARCH_URL, params=params, return_json=False)
            response = json.loads(response_text)

            # Parse response
            if isinstance(response, dict):
                results = response.get("results", [])
                count = response.get("count", len(results))
                current = response.get("current", page)
                total_pages = response.get("total_pages", 1)

                # Apply pagination
                offset = (page - 1) * limit
                paginated_results = results[offset : offset + limit]

                # Fetch abstracts for results
                pmids = [r.get("pmid") for r in paginated_results if r.get("pmid")]
                if pmids:
                    await self._add_abstracts(paginated_results, pmids)

                # Add source field
                for result in paginated_results:
                    result["source"] = "PubMed"

                return self.format_response(
                    paginated_results,
                    {
                        "count": count,
                        "page": current,
                        "page_size": limit,
                        "total_pages": total_pages,
                    },
                )

            return self.format_response([], {"error": "Unexpected response format"})

        except Exception as e:
            logger.error(f"Search failed: {e}", exc_info=True)
            return self.format_response([], {"error": f"PubMed API error: {str(e)}"})

    async def _add_abstracts(self, results: list[dict], pmids: list[int]) -> None:
        """Add abstracts to search results."""
        try:
            request_data = {
                "pmids": ",".join(str(pmid) for pmid in pmids),
                "full": "false",
            }
            # Use full URL for PubTator3 fulltext endpoint
            response_text = await self.client.post(
                PUBTATOR3_FULLTEXT_URL,
                json=request_data,
                timeout=self.timeout,
            )
            response_text.raise_for_status()
            response = json.loads(response_text.text)

            if isinstance(response, dict):
                articles = response.get("PubTator3", [])
                pmid_to_abstract = {}
                for article in articles:
                    pmid = article.get("pmid")
                    if pmid:
                        # Extract abstract from passages
                        passages = article.get("passages", [])
                        abstract_parts = []
                        for passage in passages:
                            infons = passage.get("infons", {})
                            if (
                                infons.get("section_type") == "ABSTRACT"
                                or infons.get("type") == "abstract"
                            ):
                                abstract_parts.append(passage.get("text", ""))
                        if abstract_parts:
                            pmid_to_abstract[pmid] = "\n\n".join(abstract_parts)

                # Add abstracts to results
                for result in results:
                    pmid = result.get("pmid")
                    if pmid and pmid in pmid_to_abstract:
                        result["abstract"] = pmid_to_abstract[pmid]
        except Exception as e:
            logger.warning(f"Failed to fetch abstracts: {e}")

    async def get_article(self, pmid_or_doi: str, full: bool = False) -> dict[str, Any]:
        """
        Get article details by PMID or DOI.

        Args:
            pmid_or_doi: PubMed ID (numeric) or DOI (10.xxxx/xxxx format)
            full: Whether to fetch full text

        Returns:
            Dict with article details
        """
        # Check if it's a DOI
        if self._is_doi(pmid_or_doi):
            # Use Europe PMC for DOI
            return await self._get_article_by_doi(pmid_or_doi)

        # Check if it's a PMID
        if self._is_pmid(pmid_or_doi):
            return await self._get_article_by_pmid(int(pmid_or_doi), full)

        return self.format_response(
            None,
            {
                "error": f"Invalid identifier format: {pmid_or_doi}. Expected PMID (numeric) or DOI (10.xxxx/xxxx format)"
            },
        )

    def _is_doi(self, identifier: str) -> bool:
        """Check if identifier is a DOI."""
        doi_pattern = r"^10\.\d{4,9}/[\-._;()/:\w]+$"
        return bool(re.match(doi_pattern, str(identifier)))

    def _is_pmid(self, identifier: str) -> bool:
        """Check if identifier is a PMID."""
        return str(identifier).isdigit()

    async def _get_article_by_pmid(
        self, pmid: int, full: bool = False
    ) -> dict[str, Any]:
        """Get article by PMID using PubTator3."""
        try:
            request_data = {
                "pmids": str(pmid),
                "full": str(full).lower(),
            }
            # Use full URL for PubTator3 fulltext endpoint
            response_text = await self.client.post(
                PUBTATOR3_FULLTEXT_URL,
                json=request_data,
                timeout=self.timeout,
            )
            response_text.raise_for_status()
            response = json.loads(response_text.text)

            if isinstance(response, dict):
                articles = response.get("PubTator3", [])
                if articles:
                    article = articles[0]
                    # Extract structured data
                    result = {
                        "pmid": article.get("pmid"),
                        "pmcid": article.get("pmcid"),
                        "date": article.get("date"),
                        "journal": article.get("journal"),
                        "authors": article.get("authors"),
                        "title": self._extract_title(article),
                        "abstract": self._extract_abstract(article),
                    }
                    if full:
                        result["full_text"] = self._extract_full_text(article)

                    return self.format_response(result)

            return self.format_response(None, {"error": f"Article {pmid} not found"})
        except Exception as e:
            logger.error(f"Failed to fetch article {pmid}: {e}", exc_info=True)
            return self.format_response(None, {"error": f"PubMed API error: {str(e)}"})

    def _extract_title(self, article: dict) -> str:
        """Extract title from article passages."""
        passages = article.get("passages", [])
        for passage in passages:
            infons = passage.get("infons", {})
            if infons.get("section_type") == "TITLE" or infons.get("type") == "title":
                return passage.get("text", "")
        return f"Article: {article.get('pmid')}"

    def _extract_abstract(self, article: dict) -> str:
        """Extract abstract from article passages."""
        passages = article.get("passages", [])
        abstracts = []
        for passage in passages:
            infons = passage.get("infons", {})
            if (
                infons.get("section_type") == "ABSTRACT"
                or infons.get("type") == "abstract"
            ):
                abstracts.append(passage.get("text", ""))
        return "\n\n".join(abstracts)

    def _extract_full_text(self, article: dict) -> str:
        """Extract full text from article passages."""
        passages = article.get("passages", [])
        texts = []
        for passage in passages:
            infons = passage.get("infons", {})
            section_type = infons.get("section_type", "").upper()
            if section_type in {"INTRO", "RESULTS", "METHODS", "DISCUSS", "CONCL"}:
                texts.append(passage.get("text", ""))
        return "\n\n".join(texts)

    async def _get_article_by_doi(self, doi: str) -> dict[str, Any]:
        """Get article by DOI using Europe PMC."""
        try:
            # Europe PMC search by DOI
            params = {
                "query": f'DOI:"{doi}"',
                "format": "json",
                "pageSize": 1,
            }
            response = await self._request("GET", url=f"{EUROPE_PMC_BASE_URL}/search", params=params, return_json=False)

            data = json.loads(response)
            result_list = data.get("resultList", {})
            results = result_list.get("result", [])

            if results:
                result = results[0]
                return self.format_response(
                    {
                        "doi": result.get("doi"),
                        "title": result.get("title"),
                        "authors": result.get("authorString", "").split(", ")
                        if result.get("authorString")
                        else [],
                        "journal": result.get("journalTitle"),
                        "date": result.get("pubYear"),
                        "abstract": result.get("abstractText"),
                        "source": result.get("source", "Europe PMC"),
                        "publication_state": result.get("publicationState", "preprint"),
                    }
                )

            return self.format_response(
                None, {"error": f"Article with DOI {doi} not found"}
            )
        except Exception as e:
            logger.error(f"Failed to fetch article by DOI {doi}: {e}", exc_info=True)
            return self.format_response(
                None, {"error": f"Europe PMC API error: {str(e)}"}
            )

    async def search_preprints(self, query: str, limit: int = 25) -> dict[str, Any]:
        """
        Search preprints from bioRxiv/medRxiv via Europe PMC.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            Dict with preprint results
        """
        try:
            params = {
                "query": f'{query} AND (PUB_TYPE:"Preprint" OR SOURCE:"PPR")',
                "format": "json",
                "pageSize": min(limit, 1000),
                "resultType": "core",
            }
            response = await self._request("GET", url=f"{EUROPE_PMC_BASE_URL}/search", params=params, return_json=False)

            data = json.loads(response)
            result_list = data.get("resultList", {})
            results = result_list.get("result", [])
            total = result_list.get("hitCount", len(results))

            # Format results
            formatted_results = []
            for result in results[:limit]:
                formatted_results.append(
                    {
                        "doi": result.get("doi"),
                        "title": result.get("title"),
                        "authors": result.get("authorString", "").split(", ")
                        if result.get("authorString")
                        else [],
                        "journal": f"{result.get('source', 'preprint')} (preprint)",
                        "date": result.get("pubYear"),
                        "abstract": result.get("abstractText"),
                        "source": result.get("source", "preprint"),
                        "publication_state": "preprint",
                    }
                )

            return self.format_response(
                formatted_results,
                {
                    "count": total,
                    "page_size": limit,
                },
            )
        except Exception as e:
            logger.error(f"Preprint search failed: {e}", exc_info=True)
            return self.format_response(
                [], {"error": f"Europe PMC API error: {str(e)}"}
            )
