# MCP Server API Integration Plan

## Overview

This MCP server integrates multiple biological/medical APIs to support the MS research agent and drug repurposing analysis.

## APIs to Integrate

### 1. Reactome API ✅ (Starting Point)

- **Type**: REST API
- **Authentication**: None required
- **Base URL**: https://reactome.org/ContentService
- **Documentation**: https://reactome.org/dev/content-service
- **Rate Limits**: None specified
- **Key Features**:
  - Pathway information
  - Gene/protein queries
  - Pathway analysis
  - Disease associations

### 2. KEGG API

- **Type**: REST API
- **Authentication**: None required
- **Base URL**: https://rest.kegg.jp
- **Documentation**: https://www.kegg.jp/kegg/rest/keggapi.html
- **Rate Limits**: Yes (must be respected)
- **Key Features**:
  - Pathway maps
  - Gene annotations
  - Disease information
  - Drug information

### 3. UniProt API

- **Type**: REST API
- **Authentication**: None required
- **Base URL**: https://rest.uniprot.org
- **Documentation**: https://www.uniprot.org/help/api
- **Rate Limits**: None specified
- **Key Features**:
  - Protein sequences
  - Functional annotations
  - Disease associations
  - Post-translational modifications

### 4. OMIM API

- **Type**: REST API
- **Authentication**: API key required (from omim.org)
- **Base URL**: https://api.omim.org/api
- **Documentation**: https://omim.org/help/api
- **Rate Limits**: Yes (depends on subscription)
- **Key Features**:
  - Genetic disease information
  - Gene-disease associations
  - Phenotype descriptions

### 5. GWAS Catalog API

- **Type**: REST API
- **Authentication**: None required
- **Base URL**: https://www.ebi.ac.uk/gwas/rest/api
- **Documentation**: https://www.ebi.ac.uk/gwas/docs/api
- **Rate Limits**: None specified
- **Key Features**:
  - Genetic associations
  - Variant information
  - Study metadata
  - Trait associations

### 6. Pathway Commons API ✅

- **Type**: REST API
- **Authentication**: None required
- **Base URL**: https://www.pathwaycommons.org/pc2
- **Documentation**: https://www.pathwaycommons.org/pc2/
- **Rate Limits**: None specified
- **Key Features**:
  - Integrated pathway data
  - Pathway interactions
  - Gene/protein networks

### 7. ChEMBL API ✅

- **Type**: Python library (chembl_webresource_client)
- **Authentication**: None required
- **Base URL**: N/A (uses library)
- **Documentation**: https://github.com/chembl/chembl_webresource_client
- **Rate Limits**: None specified
- **Key Features**:
  - Drug-target interactions
  - Bioactivity data
  - Mechanism of action
  - Drug indications
  - Compound information

### 8. ClinicalTrials.gov API ✅

- **Type**: REST API v2
- **Authentication**: None required
- **Base URL**: https://clinicaltrials.gov/api/v2
- **Documentation**: https://clinicaltrials.gov/api/v2/docs
- **Rate Limits**: None specified (conservative rate limiting applied)
- **Key Features**:
  - Clinical trial search
  - Study metadata
  - Trial status and outcomes
  - Condition and intervention queries

## Implementation Strategy

1. **Phase 1**: Reactome API (simplest, no auth)
2. **Phase 2**: UniProt API (no auth, similar complexity)
3. **Phase 3**: GWAS Catalog API (no auth)
4. **Phase 4**: Pathway Commons API (no auth)
5. **Phase 5**: KEGG API (rate limiting considerations)
6. **Phase 6**: OMIM API (API key required)

## Tool Naming Convention

All tools will be prefixed with the API name to make it obvious which API is being used:

- `reactome_*` - Reactome API tools
- `kegg_*` - KEGG API tools
- `uniprot_*` - UniProt API tools
- `omim_*` - OMIM API tools
- `gwas_*` - GWAS Catalog API tools
- `pathwaycommons_*` - Pathway Commons API tools
- `chembl_*` - ChEMBL API tools
- `ctg_*` - ClinicalTrials.gov API tools

## Response Format

All responses will include:

- `api_source`: The name of the API used
- `data`: The actual response data
- `metadata`: Additional metadata (timestamps, rate limit info, etc.)
