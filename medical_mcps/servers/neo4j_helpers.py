"""
Helper functions for Neo4j server response formatting and error handling.
Reduces code duplication across tool functions.
"""

import logging
from typing import Any

from ..errors import is_transient_neo4j_error

logger = logging.getLogger(__name__)

API_SOURCE = "Every Cure Matrix Knowledge Graph"


def neo4j_response(data: Any, metadata: dict[str, Any], error: str | None = None) -> dict[str, Any]:
    """Standard response format for Neo4j tools.

    Args:
        data: Response data (None if error)
        metadata: Metadata dict (must include 'database' key)
        error: Error message if error occurred

    Returns:
        Standardized response dict with api_source, data, and metadata
    """
    if error:
        return {
            "api_source": API_SOURCE,
            "data": None,
            "metadata": {"error": error, **metadata},
        }
    return {
        "api_source": API_SOURCE,
        "data": data,
        "metadata": metadata,
    }


def handle_neo4j_error(e: Exception, db_name: str, tool_name: str) -> dict[str, Any]:
    """Standard error handling for Neo4j tools.

    Args:
        e: Exception that occurred
        db_name: Database name (empty string if not applicable)
        tool_name: Name of the tool function (for logging)

    Returns:
        Standardized error response dict
    """
    if is_transient_neo4j_error(e):
        logger.warning("Tool failed: %s() - %s", tool_name, e)
    else:
        logger.error(f"Tool failed: {tool_name}() - {e}", exc_info=True)
    metadata = {"database": db_name} if db_name else {}
    return neo4j_response(
        data=None,
        metadata=metadata,
        error=f"Error in {tool_name}: {e!s}",
    )
