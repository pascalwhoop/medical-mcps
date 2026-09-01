"""FDA Orphan Drug client.

Surfaces orphan drug exclusivity and designation signals from two sources:

1. FDA Orange Book flat files (via the existing patent_client module) — the ODE
   (Orphan Drug Exclusivity) code in exclusivity.txt is the most reliable indicator
   that an application holds 7-year orphan exclusivity for a specific indication.

2. FDA OOPD designation database (accessdata.fda.gov/scripts/opdlisting) — scraped
   via a two-step HTTP form submission (GET index.cfm for cookies, then POST to
   OOPD_Results.cfm). Returns all orphan designations including pre-approval ones.

3. OpenFDA drugsfda endpoint — used to look up the sponsoring application number.

BACKGROUND: Alternatives considered (2026-04-24 scout report)
- openpharma-org/ema-mcp (https://github.com/openpharma-org/ema-mcp): MIT MCP server
  exposing get_orphan_designations, EPARs, supply shortages, PIPs from EMA's public
  JSON endpoints. No API key, refreshes 06:00/18:00 CET. Closes the EU orphan
  designation gap we currently don't cover at all — strong drop-in for an EMA tool.
- Orphanet / Orphadata API (https://github.com/Orphanet/API_Orphadata,
  https://www.orphadata.com/): rare disease + orphan drug data, RD-CODE nomenclature.
  Some bulk feeds require a Data Transfer Agreement; ema-mcp gets us 80% faster.
- EMA IRIS public register (https://iris.ema.europa.eu/odpublicregister/): the
  authoritative EU orphan opinions list. IRIS itself is sponsor-submission only;
  ema-mcp consumes the public register JSON.
- NOT: Augmented-Nature/OpenFDA-MCP-Server — verified tool list (adverse events,
  labels, NDC, recalls, drugs@FDA, shortages, devices) does NOT cover OOPD despite
  "comprehensive FDA" framing. Don't waste time integrating for orphan designations.
- US OOPD: no public REST API exists. The accessdata.fda.gov scrape (this client) is
  the only structured path. See .agents/oopd-scraping-notes.md.
"""

import logging
import re
from datetime import date
from html.parser import HTMLParser
from typing import Any

from .base_client import BaseAPIClient, log_client_error
from .patent_client import (
    _get_exclusivities,
    _get_products,
    _is_expired,
    _normalize_app_number,
    _parse_date,
)

logger = logging.getLogger(__name__)

FDA_DRUGSFDA_URL = "https://api.fda.gov/drug/drugsfda.json"
OPENFDA_DEFAULT_LIMIT = 25
OPENFDA_MAX_LIMIT = 100

OOPD_INDEX_URL = "https://www.accessdata.fda.gov/scripts/opdlisting/oopd/index.cfm"
OOPD_RESULTS_URL = "https://www.accessdata.fda.gov/scripts/opdlisting/oopd/OOPD_Results.cfm"
OOPD_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# ODE codes are numbered (e.g., "ODE-144") — match by prefix
ORPHAN_EXCLUSIVITY_PREFIX = "ODE"


class _OOPDParser(HTMLParser):
    """Parse OOPD Detailed.cfm HTML into a list of record dicts.

    Most <th> ids follow "{Field name} for Record Number {N}".
    Exception: "Exclusivity End Date" has no record number — we apply the
    most recently seen record number as a fallback.
    "Marketing Approval Date" appears twice per record; only the first (the date
    value) is captured — the second (labeled indication) overwrites but we use
    a distinct key "Approved Labeled Indication" so both are preserved.
    """

    def __init__(self):
        super().__init__()
        self._records: dict[int, dict[str, str]] = {}
        self._current_field: str | None = None
        self._current_record: int | None = None
        self._in_td = False
        self._td_text: list[str] = []
        # Track per-record how many times a field appeared (for dedup)
        self._field_seen: dict[tuple[int, str], int] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_dict = dict(attrs)
        if tag == "th":
            th_id = attr_dict.get("id", "") or ""
            m = re.search(r"^(.+?)\s+for\s+Record\s+Number\s+(\d+)$", th_id, re.IGNORECASE)
            if m:
                field = m.group(1).strip()
                rec_num = int(m.group(2))
                # "Record Number N" itself is just a row separator — skip it
                if field.lower() == "record number":
                    self._current_field = None
                    return
                self._current_record = rec_num
                if rec_num not in self._records:
                    self._records[rec_num] = {}
                # Handle duplicate field names within the same record
                key = (rec_num, field)
                count = self._field_seen.get(key, 0)
                self._field_seen[key] = count + 1
                if count == 0:
                    self._current_field = field
                else:
                    # Second "Marketing Approval Date" → rename to avoid overwrite
                    self._current_field = f"{field} (labeled indication)"
            elif th_id == "Exclusivity End Date" and self._current_record is not None:
                # No record number suffix — apply to current record
                self._current_field = "Exclusivity End Date"
            else:
                self._current_field = None
        elif tag == "td":
            self._in_td = True
            self._td_text = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "td":
            if self._in_td and self._current_field is not None and self._current_record is not None:
                text = " ".join(self._td_text).strip()
                # Strip leading &nbsp; entities that appear as non-breaking spaces
                text = text.strip("\xa0").strip()
                self._records[self._current_record][self._current_field] = text
                self._current_field = None
            self._in_td = False
            self._td_text = []

    def handle_data(self, data: str) -> None:
        if self._in_td:
            self._td_text.append(data)

    def records(self) -> list[dict[str, str]]:
        return [self._records[k] for k in sorted(self._records)]


class FDAOrphanClient(BaseAPIClient):
    """Client for FDA orphan drug exclusivity lookups."""

    def __init__(self, enable_cache: bool | None = None):
        super().__init__(
            base_url="https://api.fda.gov",
            api_name="fda_orphan",
            timeout=30.0,
            enable_cache=enable_cache,
        )

    # ------------------------------------------------------------------
    # Orange Book flat-file lookups (no network required)
    # ------------------------------------------------------------------

    async def search_orphan_exclusivity(
        self,
        drug_name: str | None = None,
        active_ingredient: str | None = None,
        application_number: str | None = None,
    ) -> dict[str, Any]:
        """Search FDA OOPD + Orange Book for orphan drug designations and exclusivity.

        Queries two sources and merges results:
        1. FDA OOPD database (accessdata.fda.gov) — all orphan designations including
           pre-approval; this is the authoritative source (~28 ivacaftor records).
        2. Orange Book ODE codes — applications with active 7-year orphan exclusivity.

        When drug_name is provided, OOPD is queried first (richer data). Orange Book
        ODE records are appended for drugs found only via application_number search.

        Args:
            drug_name: Brand or generic name to search
            active_ingredient: Active ingredient name
            application_number: NDA/BLA/ANDA number (e.g., "NDA020386")
        """
        if not any([drug_name, active_ingredient, application_number]):
            return {
                "api_source": "FDA_orange_book",
                "data": [],
                "metadata": {
                    "error": "Provide drug_name, active_ingredient, or application_number."
                },
            }

        output: list[dict[str, Any]] = []

        # ------------------------------------------------------------------
        # Source 1: OOPD scraping (when drug_name is given)
        # ------------------------------------------------------------------
        oopd_error: str | None = None
        if drug_name:
            try:
                oopd_result = await self.search_oopd_designations(drug_name=drug_name)
                for rec in oopd_result.get("data", []):
                    excl_end = rec.get("exclusivity_end_date")
                    is_active: bool | None = None
                    if excl_end:
                        is_active = not _is_expired(_parse_date(excl_end) or excl_end)
                    output.append(
                        {
                            "drug_name": rec.get("trade_name") or rec.get("generic_name", ""),
                            "active_ingredient": rec.get("generic_name", ""),
                            "applicant": rec.get("sponsor", ""),
                            "application_number": None,
                            "designation_number": rec.get("designation_number"),
                            "designation": rec.get("designation", ""),
                            "designation_status": rec.get("designation_status", ""),
                            "date_designated": rec.get("date_designated"),
                            "date_approved": rec.get("date_approved"),
                            "exclusivity_end_date": excl_end,
                            "has_active_orphan_exclusivity": is_active,
                            "source": "OOPD",
                        }
                    )
            except Exception as e:
                logger.warning("OOPD scrape failed, falling back to OB only: %s", e)
                oopd_error = str(e)

        # ------------------------------------------------------------------
        # Source 2: Orange Book ODE codes (always run for OB-only coverage)
        # ------------------------------------------------------------------
        products = _get_products()
        exclusivities = _get_exclusivities()

        orphan_excl: dict[tuple[str, str], list[dict]] = {}
        for excl in exclusivities:
            code = excl.get("Exclusivity_Code", "")
            if not code.startswith(ORPHAN_EXCLUSIVITY_PREFIX):
                continue
            key = (excl.get("Appl_Type", ""), excl.get("Appl_No", ""))
            orphan_excl.setdefault(key, []).append(excl)

        matched = list(products)
        if active_ingredient:
            q = active_ingredient.casefold()
            matched = [p for p in matched if q in p.get("Ingredient", "").casefold()]
        if drug_name:
            q = drug_name.casefold()
            matched = [
                p
                for p in matched
                if q in p.get("Trade_Name", "").casefold()
                or q in p.get("Ingredient", "").casefold()
            ]
        if application_number:
            app_type, app_no = _normalize_app_number(application_number)
            matched = [
                p
                for p in matched
                if p.get("Appl_No", "") == app_no
                and (app_type is None or p.get("Appl_Type", "") == app_type)
            ]

        seen_ob: set[tuple[str, str]] = set()
        for prod in matched:
            app_key = (prod.get("Appl_Type", ""), prod.get("Appl_No", ""))
            if app_key not in orphan_excl or app_key in seen_ob:
                continue
            seen_ob.add(app_key)

            seen_codes: set[str] = set()
            excl_records = []
            for excl in orphan_excl[app_key]:
                code_key = excl.get("Exclusivity_Code", "")
                if code_key in seen_codes:
                    continue
                seen_codes.add(code_key)
                exp = _parse_date(excl.get("Exclusivity_Date"))
                excl_records.append(
                    {
                        "code": code_key,
                        "expiry_date": exp,
                        "is_active": not _is_expired(exp) if exp else None,
                    }
                )

            output.append(
                {
                    "application_number": app_key[0] + app_key[1],
                    "drug_name": prod.get("Trade_Name", ""),
                    "active_ingredient": prod.get("Ingredient", ""),
                    "applicant": prod.get("Applicant_Full_Name") or prod.get("Applicant", ""),
                    "orphan_exclusivities": excl_records,
                    "has_active_orphan_exclusivity": any(
                        r["is_active"] for r in excl_records if r["is_active"] is not None
                    ),
                    "source": "Orange_Book_ODE",
                }
            )

        meta: dict[str, Any] = {
            "total": len(output),
            "query": {
                "drug_name": drug_name,
                "active_ingredient": active_ingredient,
                "application_number": application_number,
            },
            "note": (
                "Orange Book ODE codes represent approved 7-year orphan market exclusivity. "
                "For full orphan designation history (pre-approval), use fda_orphan_search_oopd."
            ),
        }
        if oopd_error:
            meta["oopd_error"] = oopd_error

        return {
            "api_source": "FDA_orange_book",
            "data": output,
            "metadata": meta,
        }

    # ------------------------------------------------------------------
    # FDA OOPD scraping (accessdata.fda.gov)
    # ------------------------------------------------------------------

    async def search_oopd_designations(
        self,
        drug_name: str | None = None,
        disease_name: str | None = None,
        records_per_page: int = 100,
    ) -> dict[str, Any]:
        """Search the FDA Orphan Products Designation database (OOPD).

        OOPD has no public REST API; this method scrapes the HTML form results.
        Returns all orphan designation records including pre-approval designations.
        Per the OOPD notes, ivacaftor has ~28 records across all Vertex products.

        At least one of drug_name or disease_name must be provided. Both can be
        supplied simultaneously (AND-filter).

        Args:
            drug_name: Drug/product name to search (e.g., "ivacaftor")
            disease_name: Disease/indication text to search (e.g., "cystinuria")
            records_per_page: How many records to request per page (default 100)
        """
        import httpx

        today = date.today().strftime("%m/%d/%Y")

        headers = {
            "User-Agent": OOPD_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        # Step 1: GET index.cfm to obtain Akamai bot-detection cookies
        cookies: dict[str, str] = {}
        try:
            async with httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
                headers=headers,
            ) as http:
                resp1 = await http.get(OOPD_INDEX_URL)
                cookies = dict(resp1.cookies)
                logger.info("OOPD step-1 cookies obtained: %s", list(cookies.keys()))

                # Step 2: POST form to get results; follow redirects to Detailed.cfm
                form_data = {
                    "Product_name": drug_name or "",
                    "sponsor_name": "",
                    "Designation": disease_name or "",
                    "Designation_Start_Date": "01/01/1983",
                    "Designation_End_Date": today,
                    "Search_param": "DESDATE",
                    "Output_Format": "Detailed",
                    "Sort_order": "Date_Reverse_Order",
                    "RecordsPerPage": str(records_per_page),
                    "newSearch": "Run Search",
                }
                resp2 = await http.post(
                    OOPD_RESULTS_URL,
                    data=form_data,
                    cookies=cookies,
                    headers={**headers, "Referer": OOPD_INDEX_URL},
                )
                final_url = str(resp2.url)
                logger.info("OOPD step-2 final URL: %s", final_url)

                # If redirected back to index, the search returned no results
                if "Detailed.cfm" not in final_url and "OOPD_Results" not in final_url:
                    logger.warning("OOPD search redirected to %s — no results", final_url)
                    return {
                        "api_source": "FDA_OOPD",
                        "data": [],
                        "metadata": {
                            "total": 0,
                            "query": {"drug_name": drug_name, "disease_name": disease_name},
                            "note": "OOPD returned no results (redirected to index page)",
                        },
                    }

                html = resp2.text
        except Exception as e:
            logger.error("OOPD HTTP request failed: %s", e, exc_info=True)
            return {
                "api_source": "FDA_OOPD",
                "data": [],
                "metadata": {"error": f"OOPD request failed: {e!s}"},
            }

        # Parse the HTML
        parser = _OOPDParser()
        parser.feed(html)
        raw_records = parser.records()
        logger.info(
            "OOPD parsed %d records for drug_name=%s disease_name=%s",
            len(raw_records),
            drug_name,
            disease_name,
        )

        def _norm(r: dict[str, str]) -> dict[str, Any]:
            # Actual <th id> field names from OOPD Detailed.cfm DOM (verified 2026-04-25):
            # "Generic name", "Trade Name", "Date designated", "Orphan designation",
            # "Orphan designation status", "Marketing Approval Date",
            # "Exclusivity End Date" (no record number suffix), "Sponsor"
            return {
                "generic_name": r.get("Generic name", ""),
                "trade_name": r.get("Trade Name", ""),
                "date_designated": r.get("Date designated", "") or None,
                "designation": r.get("Orphan designation", ""),
                "sponsor": r.get("Sponsor", ""),
                "designation_status": r.get("Orphan designation status", ""),
                "date_approved": r.get("Marketing Approval Date", "") or None,
                "exclusivity_end_date": (
                    v if (v := r.get("Exclusivity End Date", "")) and v.upper() != "TBD" else None
                ),
                "designation_number": None,  # not present in Detailed.cfm HTML
            }

        data = [_norm(r) for r in raw_records]
        return {
            "api_source": "FDA_OOPD",
            "data": data,
            "metadata": {
                "total": len(data),
                "query": {"drug_name": drug_name, "disease_name": disease_name},
                "note": (
                    "Source: FDA Orphan Products Designation database (OOPD). "
                    "Includes pre-approval designations; not limited to approved drugs."
                ),
            },
        }

    # ------------------------------------------------------------------
    # OpenFDA drugsfda lookup (live API)
    # ------------------------------------------------------------------

    async def get_application_details(
        self,
        drug_name: str | None = None,
        active_ingredient: str | None = None,
        application_number: str | None = None,
        limit: int = OPENFDA_DEFAULT_LIMIT,
    ) -> dict[str, Any]:
        """Fetch application details from FDA drugsfda for a drug.

        Useful for finding the sponsoring NDA/BLA, submission history,
        and product marketing status. Cross-reference with
        search_orphan_exclusivity() to confirm ODE status.

        Args:
            drug_name: Brand or generic name
            active_ingredient: Active ingredient name
            application_number: NDA/BLA number (e.g., "NDA021588")
            limit: Max results (default 25)
        """
        search_parts = []
        if drug_name:
            search_parts.append(
                f'(openfda.brand_name:"{drug_name}" OR openfda.generic_name:"{drug_name}")'
            )
        if active_ingredient:
            search_parts.append(f'openfda.generic_name:"{active_ingredient}"')
        if application_number:
            search_parts.append(f'application_number:"{application_number}"')

        if not search_parts:
            return {
                "api_source": "FDA_drugsfda",
                "data": [],
                "metadata": {
                    "error": "Provide drug_name, active_ingredient, or application_number."
                },
            }

        params = {
            "search": " AND ".join(search_parts),
            "limit": min(limit, OPENFDA_MAX_LIMIT),
        }

        try:
            response = await self._request("GET", url=FDA_DRUGSFDA_URL, params=params)
            results = response.get("results", []) if isinstance(response, dict) else []
            meta = response.get("meta", {}).get("results", {}) if isinstance(response, dict) else {}

            formatted = []
            for r in results:
                openfda = r.get("openfda", {})
                formatted.append(
                    {
                        "application_number": r.get("application_number"),
                        "sponsor_name": r.get("sponsor_name"),
                        "brand_names": openfda.get("brand_name", []),
                        "generic_names": openfda.get("generic_name", []),
                        "products": [
                            {
                                "product_number": p.get("product_number"),
                                "brand_name": p.get("brand_name"),
                                "active_ingredients": p.get("active_ingredients", []),
                                "dosage_form": p.get("dosage_form"),
                                "route": p.get("route"),
                                "marketing_status": p.get("marketing_status"),
                                "reference_drug": p.get("reference_drug"),
                            }
                            for p in r.get("products", [])[:5]
                        ],
                    }
                )

            return {
                "api_source": "FDA_drugsfda",
                "data": formatted,
                "metadata": {
                    "total": meta.get("total", len(formatted)),
                    "query": {
                        "drug_name": drug_name,
                        "active_ingredient": active_ingredient,
                        "application_number": application_number,
                    },
                },
            }
        except Exception as e:
            log_client_error(logger, f"FDA drugsfda lookup failed: {e}", e)
            return {
                "api_source": "FDA_drugsfda",
                "data": [],
                "metadata": {
                    "error": "No matches found" if "HTTP 404" in str(e) else f"FDA API error: {e!s}"
                },
            }
