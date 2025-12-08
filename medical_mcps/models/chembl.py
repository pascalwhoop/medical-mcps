"""
Pydantic models for ChEMBL API responses.

Models derived from sample API responses.
Following 80/20 principle: capture main structure, allow flexibility for edge cases.
"""

from typing import Any, Optional
from pydantic import BaseModel

from .base import MCPToolResult


class ChEMBLMolecule(BaseModel):
    """ChEMBL molecule model"""
    molecule_chembl_id: str
    pref_name: Optional[str] = None
    molecule_type: Optional[str] = None
    max_phase: Optional[int] = None
    first_approval: Optional[int] = None
    molecular_weight: Optional[float] = None
    alogp: Optional[float] = None
    
    class Config:
        extra = "allow"


class ChEMBLTarget(BaseModel):
    """ChEMBL target model"""
    target_chembl_id: str
    pref_name: Optional[str] = None
    target_type: Optional[str] = None
    organism: Optional[str] = None
    
    class Config:
        extra = "allow"


class ChEMBLActivity(BaseModel):
    """ChEMBL activity model"""
    activity_id: Optional[int] = None
    molecule_chembl_id: Optional[str] = None
    target_chembl_id: Optional[str] = None
    standard_value: Optional[float] = None
    standard_type: Optional[str] = None
    standard_units: Optional[str] = None
    assay_chembl_id: Optional[str] = None
    
    class Config:
        extra = "allow"


class ChEMBLMechanism(BaseModel):
    """ChEMBL mechanism model"""
    mechanism_id: Optional[int] = None
    molecule_chembl_id: Optional[str] = None
    target_chembl_id: Optional[str] = None
    mechanism_of_action: Optional[str] = None
    action_type: Optional[str] = None
    
    class Config:
        extra = "allow"


class ChEMBLDrugIndication(BaseModel):
    """ChEMBL drug indication model"""
    drug_chembl_id: Optional[str] = None
    molecule_chembl_id: Optional[str] = None
    parent_molecule_chembl_id: Optional[str] = None
    mesh_heading: Optional[str] = None
    mesh_id: Optional[str] = None
    efo_id: Optional[str] = None
    efo_term: Optional[str] = None
    max_phase_for_ind: Optional[int] = None
    indication_refs: Optional[list[Any]] = None
    
    class Config:
        extra = "allow"


class ChEMBLToolResult(MCPToolResult[ChEMBLMolecule]):
    """ChEMBL-specific MCP tool result"""
    pass
