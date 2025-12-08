"""
Pydantic models for MyVariant API responses.

Models derived from sample API responses.
Following 80/20 principle: capture main structure, allow flexibility for edge cases.
"""

from typing import Any, Optional
from pydantic import BaseModel

from .base import MCPToolResult


class MyVariantVariant(BaseModel):
    """MyVariant variant model"""
    _id: Optional[str] = None
    query: Optional[str] = None
    dbsnp: Optional[dict[str, Any]] = None
    clinvar: Optional[dict[str, Any]] = None
    gnomad_exome: Optional[dict[str, Any]] = None
    gnomad_genome: Optional[dict[str, Any]] = None
    cadd: Optional[dict[str, Any]] = None
    dbnsfp: Optional[dict[str, Any]] = None
    
    class Config:
        extra = "allow"


class MyVariantSearchResult(BaseModel):
    """MyVariant search result model"""
    hits: Optional[list[MyVariantVariant]] = None
    total: Optional[int] = None
    
    class Config:
        extra = "allow"


class MyVariantToolResult(MCPToolResult[MyVariantVariant]):
    """MyVariant-specific MCP tool result"""
    pass
