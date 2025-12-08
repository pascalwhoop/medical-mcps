"""
Pydantic models for ClinicalTrials.gov API responses.

Models derived from sample API responses.
Following 80/20 principle: capture main structure, allow flexibility for edge cases.
"""

from typing import Any, Optional
from pydantic import BaseModel

from .base import MCPToolResult


class CTGStudy(BaseModel):
    """ClinicalTrials.gov study model"""
    nctId: Optional[str] = None
    protocolSection: Optional[dict[str, Any]] = None
    derivedSection: Optional[dict[str, Any]] = None
    hasResults: Optional[bool] = None
    
    class Config:
        extra = "allow"


class CTGSearchResult(BaseModel):
    """ClinicalTrials.gov search result model"""
    studies: Optional[list[CTGStudy]] = None
    nextPageToken: Optional[str] = None
    totalCount: Optional[int] = None
    
    class Config:
        extra = "allow"


class CTGToolResult(MCPToolResult[CTGStudy]):
    """ClinicalTrials.gov-specific MCP tool result"""
    pass
