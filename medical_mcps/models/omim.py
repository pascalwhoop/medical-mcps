"""
Pydantic models for OMIM API responses.

Models derived from sample API responses.
Following 80/20 principle: capture main structure, allow flexibility for edge cases.
"""

from typing import Any, Optional
from pydantic import BaseModel

from .base import MCPToolResult


class OMIMEntry(BaseModel):
    """OMIM entry model"""
    mimNumber: Optional[str] = None
    preferredTitle: Optional[str] = None
    allelicVariantList: Optional[list[dict[str, Any]]] = None
    geneMap: Optional[dict[str, Any]] = None
    text: Optional[list[dict[str, Any]]] = None
    
    class Config:
        extra = "allow"


class OMIMSearchResult(BaseModel):
    """OMIM search result model"""
    omim: Optional[dict[str, Any]] = None
    searchResponse: Optional[dict[str, Any]] = None
    
    class Config:
        extra = "allow"


class OMIMToolResult(MCPToolResult[OMIMEntry]):
    """OMIM-specific MCP tool result"""
    pass
