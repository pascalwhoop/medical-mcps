"""
Pydantic models for NCI Clinical Trials API responses.

Models derived from sample API responses.
Following 80/20 principle: capture main structure, allow flexibility for edge cases.
"""

from typing import Any, Optional
from pydantic import BaseModel

from .base import MCPToolResult


class NCITrial(BaseModel):
    """NCI trial model"""
    nct_id: Optional[str] = None
    protocol_id: Optional[str] = None
    nci_id: Optional[str] = None
    official_title: Optional[str] = None
    brief_title: Optional[str] = None
    current_trial_status: Optional[str] = None
    lead_org: Optional[dict[str, Any]] = None
    primary_disease_names: Optional[list[str]] = None
    intervention_names: Optional[list[str]] = None
    phase: Optional[list[str]] = None
    
    class Config:
        extra = "allow"


class NCISearchResult(BaseModel):
    """NCI search result model"""
    data: Optional[list[NCITrial]] = None
    total: Optional[int] = None
    
    class Config:
        extra = "allow"


class NCIToolResult(MCPToolResult[NCITrial]):
    """NCI-specific MCP tool result"""
    pass
