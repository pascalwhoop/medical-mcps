"""
Pydantic models for OpenFDA API responses.

Models derived from sample API responses.
Following 80/20 principle: capture main structure, allow flexibility for edge cases.
"""

from typing import Any, Optional
from pydantic import BaseModel

from .base import MCPToolResult


class OpenFDAAdverseEvent(BaseModel):
    """OpenFDA adverse event model"""
    safetyreportid: Optional[str] = None
    serious: Optional[int] = None
    receivedate: Optional[str] = None
    drugs: Optional[list[dict[str, Any]]] = None
    reactions: Optional[list[str]] = None
    patient: Optional[dict[str, Any]] = None
    summary: Optional[str] = None
    
    class Config:
        extra = "allow"


class OpenFDADrugLabel(BaseModel):
    """OpenFDA drug label model"""
    set_id: Optional[str] = None
    brand_name: Optional[str] = None
    generic_name: Optional[str] = None
    indications_and_usage: Optional[list[str]] = None
    boxed_warning: Optional[list[str]] = None
    dosage_and_administration: Optional[list[str]] = None
    contraindications: Optional[list[str]] = None
    warnings_and_precautions: Optional[list[str]] = None
    adverse_reactions: Optional[list[str]] = None
    drug_interactions: Optional[list[str]] = None
    
    class Config:
        extra = "allow"


class OpenFDAToolResult(MCPToolResult[OpenFDAAdverseEvent]):
    """OpenFDA-specific MCP tool result"""
    pass
