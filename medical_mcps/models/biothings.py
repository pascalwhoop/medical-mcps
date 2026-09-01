"""
Pydantic models for BioThings API responses (MyGene, MyDisease, MyChem).

Models derived from sample API responses.
Following 80/20 principle: capture main structure, allow flexibility for edge cases.
"""

from typing import Any

from pydantic import BaseModel, field_validator

from .base import MCPToolResult


class MyGeneGene(BaseModel):
    """MyGene gene model"""

    _id: str | None = None
    symbol: str | None = None
    name: str | None = None
    taxid: int | None = None
    entrezgene: str | None = None
    ensembl: dict[str, Any] | None = None
    uniprot: dict[str, Any] | None = None
    alias: list[str] | None = None

    @field_validator("ensembl", mode="before")
    @classmethod
    def coerce_ensembl(cls, value: Any) -> Any:
        if isinstance(value, list):
            if not value:
                return None
            if isinstance(value[0], dict):
                return value[0]
        return value

    @field_validator("alias", mode="before")
    @classmethod
    def coerce_alias(cls, value: Any) -> Any:
        if isinstance(value, str):
            return [value]
        return value

    class Config:
        extra = "allow"


class MyDiseaseDisease(BaseModel):
    """MyDisease disease model"""

    _id: str | None = None
    name: str | None = None
    mondo: dict[str, Any] | None = None
    doid: dict[str, Any] | None = None
    umls: dict[str, Any] | None = None
    synonyms: list[str] | None = None

    class Config:
        extra = "allow"


class MyChemDrug(BaseModel):
    """MyChem drug model"""

    _id: str | None = None
    name: str | None = None
    drugbank: dict[str, Any] | None = None
    chembl: dict[str, Any] | None = None
    pubchem: dict[str, Any] | None = None
    unii: str | dict[str, Any] | None = None  # Can be string or dict

    @field_validator("unii", mode="before")
    @classmethod
    def coerce_unii(cls, value: Any) -> Any:
        if isinstance(value, list):
            if not value:
                return None
            if isinstance(value[0], str):
                return value[0]
        return value

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
