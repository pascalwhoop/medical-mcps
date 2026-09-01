"""Tests for shared MCP/API error envelopes."""

from medical_mcps.errors import (
    CLIENT_ERROR_TYPE,
    UPSTREAM_ERROR_TYPE,
    suggest_tools,
    unknown_tool_response,
    upstream_error_metadata,
)


def test_unknown_tool_response_includes_suggestions():
    response = unknown_tool_response(
        "opentargets_get_target",
        [
            "opentargets_search",
            "opentargets_get_associations",
            "chembl_search_molecules",
        ],
    )
    assert response["metadata"]["error_type"] == CLIENT_ERROR_TYPE
    assert "opentargets_search" in response["metadata"]["suggestions"]


def test_suggest_tools_prefers_prefix_matches():
    suggestions = suggest_tools(
        "chembl_search",
        ["chembl_search_molecules", "chembl_get_molecule", "pubmed_search_articles"],
    )
    assert suggestions[0].startswith("chembl_")


def test_upstream_error_metadata_shape():
    metadata = upstream_error_metadata(
        api_name="Pathway Commons",
        detail="HTTP 502 Bad Gateway",
        status_code=502,
    )
    assert metadata["error_type"] == UPSTREAM_ERROR_TYPE
    assert metadata["upstream_status"] == 502
