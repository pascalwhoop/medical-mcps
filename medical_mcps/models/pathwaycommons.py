"""
Pydantic models for Pathway Commons API responses.

Models derived from sample API responses.
Following 80/20 principle: capture main structure, allow flexibility for edge cases.
"""

from typing import Any, Optional
from pydantic import BaseModel

from .base import MCPToolResult


class PathwayCommonsPathway(BaseModel):
    """Pathway Commons pathway model"""
    uri: Optional[str] = None
    name: Optional[str] = None
    displayName: Optional[str] = None
    datasource: Optional[str] = None
    organism: Optional[str] = None
    pathwayType: Optional[str] = None
    
    class Config:
        extra = "allow"


class PathwayCommonsSearchResult(BaseModel):
    """Pathway Commons search result model"""
    hits: Optional[list[PathwayCommonsPathway]] = None
    total: Optional[int] = None
    
    class Config:
        extra = "allow"


class PathwayCommonsToolResult(MCPToolResult[PathwayCommonsPathway]):
    """Pathway Commons-specific MCP tool result"""
    pass
