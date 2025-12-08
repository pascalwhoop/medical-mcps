"""
Pydantic models for OpenTargets API responses.

Models derived from sample API responses.
Following 80/20 principle: capture main structure, allow flexibility for edge cases.
"""

from typing import Any, Optional
from pydantic import BaseModel

from .base import MCPToolResult


class OpenTargetsAssociation(BaseModel):
    """OpenTargets association model"""
    target: Optional[dict[str, Any]] = None
    disease: Optional[dict[str, Any]] = None
    association_score: Optional[dict[str, Any]] = None
    datatype_scores: Optional[dict[str, Any]] = None
    
    class Config:
        extra = "allow"


class OpenTargetsSearchResult(BaseModel):
    """OpenTargets search result model"""
    data: Optional[list[dict[str, Any]]] = None
    total: Optional[int] = None
    
    class Config:
        extra = "allow"


class OpenTargetsToolResult(MCPToolResult[OpenTargetsAssociation]):
    """OpenTargets-specific MCP tool result"""
    pass
