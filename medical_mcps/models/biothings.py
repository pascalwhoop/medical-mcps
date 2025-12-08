"""
Pydantic models for BioThings API responses (MyGene, MyDisease, MyChem).

Models derived from sample API responses.
Following 80/20 principle: capture main structure, allow flexibility for edge cases.
"""

from typing import Any, Optional
from pydantic import BaseModel

from .base import MCPToolResult


class MyGeneGene(BaseModel):
    """MyGene gene model"""
    _id: Optional[str] = None
    symbol: Optional[str] = None
    name: Optional[str] = None
    taxid: Optional[int] = None
    entrezgene: Optional[str] = None
    ensembl: Optional[dict[str, Any]] = None
    uniprot: Optional[dict[str, Any]] = None
    alias: Optional[list[str]] = None
    
    class Config:
        extra = "allow"


class MyDiseaseDisease(BaseModel):
    """MyDisease disease model"""
    _id: Optional[str] = None
    name: Optional[str] = None
    mondo: Optional[dict[str, Any]] = None
    doid: Optional[dict[str, Any]] = None
    umls: Optional[dict[str, Any]] = None
    synonyms: Optional[list[str]] = None
    
    class Config:
        extra = "allow"


class MyChemDrug(BaseModel):
    """MyChem drug model"""
    _id: Optional[str] = None
    name: Optional[str] = None
    drugbank: Optional[dict[str, Any]] = None
    chembl: Optional[dict[str, Any]] = None
    pubchem: Optional[dict[str, Any]] = None
    unii: Optional[str] = None
    
    class Config:
        extra = "allow"


class MyGeneToolResult(MCPToolResult[MyGeneGene]):
    """MyGene-specific MCP tool result"""
    pass


class MyDiseaseToolResult(MCPToolResult[MyDiseaseDisease]):
    """MyDisease-specific MCP tool result"""
    pass


class MyChemToolResult(MCPToolResult[MyChemDrug]):
    """MyChem-specific MCP tool result"""
    pass
