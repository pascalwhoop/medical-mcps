#!/usr/bin/env python3
"""
Unified Biological APIs MCP Server
Combines all tools from all API servers into a single endpoint at /tools/unified/mcp
"""

import logging

from mcp.server.fastmcp import FastMCP

# Import all tool functions from individual servers
from .reactome_server import (
    get_pathway as reactome_get_pathway_impl,
    query_pathways as reactome_query_pathways_impl,
    get_pathway_participants as reactome_get_pathway_participants_impl,
    get_disease_pathways as reactome_get_disease_pathways_impl,
)
from .kegg_server import (
    get_pathway_info as kegg_get_pathway_info_impl,
    list_pathways as kegg_list_pathways_impl,
    find_pathways as kegg_find_pathways_impl,
    get_gene as kegg_get_gene_impl,
    find_genes as kegg_find_genes_impl,
    get_disease as kegg_get_disease_impl,
    find_diseases as kegg_find_diseases_impl,
    link_pathway_genes as kegg_link_pathway_genes_impl,
)
from .uniprot_server import (
    get_protein as uniprot_get_protein_impl,
    search_proteins as uniprot_search_proteins_impl,
    get_protein_sequence as uniprot_get_protein_sequence_impl,
    get_disease_associations as uniprot_get_disease_associations_impl,
    map_ids as uniprot_map_ids_impl,
)
from .omim_server import (
    get_entry as omim_get_entry_impl,
    search_entries as omim_search_entries_impl,
    get_gene as omim_get_gene_impl,
    search_genes as omim_search_genes_impl,
    get_phenotype as omim_get_phenotype_impl,
    search_phenotypes as omim_search_phenotypes_impl,
)
from .gwas_server import (
    get_association as gwas_get_association_impl,
    search_associations as gwas_search_associations_impl,
    get_variant as gwas_get_variant_impl,
    search_variants as gwas_search_variants_impl,
    get_study as gwas_get_study_impl,
    search_studies as gwas_search_studies_impl,
    get_trait as gwas_get_trait_impl,
    search_traits as gwas_search_traits_impl,
)
from .pathwaycommons_server import (
    search_pathwaycommons as pathwaycommons_search_impl,
    get_pathway_by_uri as pathwaycommons_get_pathway_by_uri_impl,
    top_pathways as pathwaycommons_top_pathways_impl,
    graph as pathwaycommons_graph_impl,
    traverse as pathwaycommons_traverse_impl,
)
from .chembl_server import (
    get_molecule as chembl_get_molecule_impl,
    search_molecules as chembl_search_molecules_impl,
    get_target as chembl_get_target_impl,
    search_targets as chembl_search_targets_impl,
    get_activities as chembl_get_activities_impl,
    get_mechanism as chembl_get_mechanism_impl,
    find_drugs_by_target as chembl_find_drugs_by_target_impl,
    find_drugs_by_indication as chembl_find_drugs_by_indication_impl,
    get_drug_indications as chembl_get_drug_indications_impl,
)
from .ctg_server import (
    search_studies as ctg_search_studies_impl,
    get_study as ctg_get_study_impl,
    search_by_condition as ctg_search_by_condition_impl,
    search_by_intervention as ctg_search_by_intervention_impl,
    get_study_metadata as ctg_get_study_metadata_impl,
)

logger = logging.getLogger(__name__)

# Create unified FastMCP server
unified_mcp = FastMCP(
    "biological-apis-unified",
    stateless_http=True,
    json_response=True,
)

# Register all Reactome tools
@unified_mcp.tool(name="reactome_get_pathway")
async def reactome_get_pathway(pathway_id: str) -> dict:
    """Get pathway information from Reactome API."""
    return await reactome_get_pathway_impl(pathway_id)

@unified_mcp.tool(name="reactome_query_pathways")
async def reactome_query_pathways(query: str, species: str = "Homo sapiens") -> dict:
    """Query pathways from Reactome API by keyword or gene/protein name."""
    return await reactome_query_pathways_impl(query, species)

@unified_mcp.tool(name="reactome_get_pathway_participants")
async def reactome_get_pathway_participants(pathway_id: str) -> dict | list:
    """Get all participants (genes, proteins, small molecules) in a Reactome pathway."""
    return await reactome_get_pathway_participants_impl(pathway_id)

@unified_mcp.tool(name="reactome_get_disease_pathways")
async def reactome_get_disease_pathways(disease_name: str) -> dict | list:
    """Get pathways associated with a disease from Reactome API."""
    return await reactome_get_disease_pathways_impl(disease_name)

# Register all KEGG tools
@unified_mcp.tool(name="kegg_get_pathway_info")
async def kegg_get_pathway_info(pathway_id: str) -> str:
    """Get pathway information from KEGG by pathway ID."""
    return await kegg_get_pathway_info_impl(pathway_id)

@unified_mcp.tool(name="kegg_list_pathways")
async def kegg_list_pathways(organism: str | None = None) -> str:
    """List pathways from KEGG."""
    return await kegg_list_pathways_impl(organism)

@unified_mcp.tool(name="kegg_find_pathways")
async def kegg_find_pathways(query: str) -> str:
    """Find pathways in KEGG matching a query keyword."""
    return await kegg_find_pathways_impl(query)

@unified_mcp.tool(name="kegg_get_gene")
async def kegg_get_gene(gene_id: str) -> str:
    """Get gene information from KEGG by gene ID."""
    return await kegg_get_gene_impl(gene_id)

@unified_mcp.tool(name="kegg_find_genes")
async def kegg_find_genes(query: str, organism: str | None = None) -> str:
    """Find genes in KEGG matching a query keyword."""
    return await kegg_find_genes_impl(query, organism)

@unified_mcp.tool(name="kegg_get_disease")
async def kegg_get_disease(disease_id: str) -> str:
    """Get disease information from KEGG by disease ID."""
    return await kegg_get_disease_impl(disease_id)

@unified_mcp.tool(name="kegg_find_diseases")
async def kegg_find_diseases(query: str) -> str:
    """Find diseases in KEGG matching a query keyword."""
    return await kegg_find_diseases_impl(query)

@unified_mcp.tool(name="kegg_link_pathway_genes")
async def kegg_link_pathway_genes(pathway_id: str) -> str:
    """Get genes linked to a KEGG pathway."""
    return await kegg_link_pathway_genes_impl(pathway_id)

# Register all UniProt tools
@unified_mcp.tool(name="uniprot_get_protein")
async def uniprot_get_protein(accession: str, format: str = "json") -> dict | str:
    """Get protein information from UniProt by accession."""
    return await uniprot_get_protein_impl(accession, format)

@unified_mcp.tool(name="uniprot_search_proteins")
async def uniprot_search_proteins(
    query: str, format: str = "json", limit: int = 25, offset: int = 0
) -> dict | str:
    """Search proteins in UniProtKB."""
    return await uniprot_search_proteins_impl(query, format, limit, offset)

@unified_mcp.tool(name="uniprot_get_protein_sequence")
async def uniprot_get_protein_sequence(accession: str) -> str:
    """Get protein sequence in FASTA format."""
    return await uniprot_get_protein_sequence_impl(accession)

@unified_mcp.tool(name="uniprot_get_disease_associations")
async def uniprot_get_disease_associations(accession: str) -> dict:
    """Get disease associations for a protein."""
    return await uniprot_get_disease_associations_impl(accession)

@unified_mcp.tool(name="uniprot_map_ids")
async def uniprot_map_ids(from_db: str, to_db: str, ids: str) -> dict | str:
    """Map identifiers between databases using UniProt ID mapping."""
    return await uniprot_map_ids_impl(from_db, to_db, ids)

# Register all OMIM tools
@unified_mcp.tool(name="omim_get_entry")
async def omim_get_entry(mim_number: str, api_key: str, include: str = "text") -> dict:
    """Get entry information from OMIM by MIM number."""
    return await omim_get_entry_impl(mim_number, api_key, include)

@unified_mcp.tool(name="omim_search_entries")
async def omim_search_entries(
    search: str,
    api_key: str,
    include: str = "text",
    limit: int = 20,
    start: int = 0
) -> dict:
    """Search entries in OMIM."""
    return await omim_search_entries_impl(search, api_key, include, limit, start)

@unified_mcp.tool(name="omim_get_gene")
async def omim_get_gene(gene_symbol: str, api_key: str, include: str = "geneMap") -> dict:
    """Get gene information from OMIM by gene symbol."""
    return await omim_get_gene_impl(gene_symbol, api_key, include)

@unified_mcp.tool(name="omim_search_genes")
async def omim_search_genes(
    search: str,
    api_key: str,
    include: str = "geneMap",
    limit: int = 20,
    start: int = 0
) -> dict:
    """Search genes in OMIM."""
    return await omim_search_genes_impl(search, api_key, include, limit, start)

@unified_mcp.tool(name="omim_get_phenotype")
async def omim_get_phenotype(mim_number: str, api_key: str, include: str = "text") -> dict:
    """Get phenotype information from OMIM by MIM number."""
    return await omim_get_phenotype_impl(mim_number, api_key, include)

@unified_mcp.tool(name="omim_search_phenotypes")
async def omim_search_phenotypes(
    search: str,
    api_key: str,
    include: str = "text",
    limit: int = 20,
    start: int = 0
) -> dict:
    """Search phenotypes in OMIM."""
    return await omim_search_phenotypes_impl(search, api_key, include, limit, start)

# Register all GWAS tools
@unified_mcp.tool(name="gwas_get_association")
async def gwas_get_association(association_id: str) -> dict:
    """Get association information from GWAS Catalog by ID."""
    return await gwas_get_association_impl(association_id)

@unified_mcp.tool(name="gwas_search_associations")
async def gwas_search_associations(
    query: str = None,
    variant_id: str = None,
    study_id: str = None,
    trait: str = None,
    size: int = 20,
    page: int = 0,
) -> dict:
    """Search for associations in GWAS Catalog."""
    return await gwas_search_associations_impl(query, variant_id, study_id, trait, size, page)

@unified_mcp.tool(name="gwas_get_variant")
async def gwas_get_variant(variant_id: str) -> dict:
    """Get single nucleotide polymorphism (SNP) information from GWAS Catalog by rsId."""
    return await gwas_get_variant_impl(variant_id)

@unified_mcp.tool(name="gwas_search_variants")
async def gwas_search_variants(query: str = None, size: int = 20, page: int = 0) -> dict:
    """Search for SNPs/variants in GWAS Catalog by rsId."""
    return await gwas_search_variants_impl(query, size, page)

@unified_mcp.tool(name="gwas_get_study")
async def gwas_get_study(study_id: str) -> dict:
    """Get study information from GWAS Catalog by ID."""
    return await gwas_get_study_impl(study_id)

@unified_mcp.tool(name="gwas_search_studies")
async def gwas_search_studies(
    query: str = None, trait: str = None, size: int = 20, page: int = 0
) -> dict:
    """Search for studies in GWAS Catalog."""
    return await gwas_search_studies_impl(query, trait, size, page)

@unified_mcp.tool(name="gwas_get_trait")
async def gwas_get_trait(trait_id: str) -> dict:
    """Get trait information from GWAS Catalog by ID."""
    return await gwas_get_trait_impl(trait_id)

@unified_mcp.tool(name="gwas_search_traits")
async def gwas_search_traits(query: str = None, size: int = 20, page: int = 0) -> dict:
    """Search for traits in GWAS Catalog."""
    return await gwas_search_traits_impl(query, size, page)

# Register all Pathway Commons tools
@unified_mcp.tool(name="pathwaycommons_search")
async def pathwaycommons_search(
    q: str,
    type: str = "Pathway",
    format: str = "json",
    page: int = 0,
    datasource: str = None,
) -> dict:
    """Search Pathway Commons for pathways, proteins, or other biological entities."""
    return await pathwaycommons_search_impl(q, type, format, page, datasource)

@unified_mcp.tool(name="pathwaycommons_get_pathway_by_uri")
async def pathwaycommons_get_pathway_by_uri(uri: str, format: str = "json") -> dict | str:
    """Get pathway information from Pathway Commons by URI."""
    return await pathwaycommons_get_pathway_by_uri_impl(uri, format)

@unified_mcp.tool(name="pathwaycommons_top_pathways")
async def pathwaycommons_top_pathways(
    gene: str = None, datasource: str = None, limit: int = 10
) -> dict:
    """Get top-level pathways from Pathway Commons using v2 POST API."""
    return await pathwaycommons_top_pathways_impl(gene, datasource, limit)

@unified_mcp.tool(name="pathwaycommons_graph")
async def pathwaycommons_graph(
    source: str,
    target: str = None,
    kind: str = "neighborhood",
    limit: int = 1,
    format: str = "json",
) -> dict | str:
    """Get pathway graph/network from Pathway Commons using v2 POST API."""
    return await pathwaycommons_graph_impl(source, target, kind, limit, format)

@unified_mcp.tool(name="pathwaycommons_traverse")
async def pathwaycommons_traverse(uri: str, path: str, format: str = "json") -> dict | str:
    """Traverse pathway data in Pathway Commons using v2 POST API."""
    return await pathwaycommons_traverse_impl(uri, path, format)

# Register all ChEMBL tools
@unified_mcp.tool(name="chembl_get_molecule")
async def chembl_get_molecule(molecule_chembl_id: str) -> dict:
    """Get molecule (drug/compound) information from ChEMBL by ChEMBL ID."""
    return await chembl_get_molecule_impl(molecule_chembl_id)

@unified_mcp.tool(name="chembl_search_molecules")
async def chembl_search_molecules(query: str, limit: int = 20) -> dict:
    """Search molecules (drugs/compounds) in ChEMBL by name or synonym."""
    return await chembl_search_molecules_impl(query, limit)

@unified_mcp.tool(name="chembl_get_target")
async def chembl_get_target(target_chembl_id: str) -> dict:
    """Get target (protein) information from ChEMBL by ChEMBL ID."""
    return await chembl_get_target_impl(target_chembl_id)

@unified_mcp.tool(name="chembl_search_targets")
async def chembl_search_targets(query: str, limit: int = 20) -> dict:
    """Search targets (proteins) in ChEMBL by name or synonym."""
    return await chembl_search_targets_impl(query, limit)

@unified_mcp.tool(name="chembl_get_activities")
async def chembl_get_activities(
    target_chembl_id: str = None,
    molecule_chembl_id: str = None,
    limit: int = 50,
) -> dict:
    """Get bioactivity data from ChEMBL."""
    return await chembl_get_activities_impl(target_chembl_id, molecule_chembl_id, limit)

@unified_mcp.tool(name="chembl_get_mechanism")
async def chembl_get_mechanism(molecule_chembl_id: str) -> dict:
    """Get mechanism of action for a molecule from ChEMBL."""
    return await chembl_get_mechanism_impl(molecule_chembl_id)

@unified_mcp.tool(name="chembl_find_drugs_by_target")
async def chembl_find_drugs_by_target(target_chembl_id: str, limit: int = 50) -> dict:
    """Find all drugs/compounds targeting a specific protein."""
    return await chembl_find_drugs_by_target_impl(target_chembl_id, limit)

@unified_mcp.tool(name="chembl_find_drugs_by_indication")
async def chembl_find_drugs_by_indication(disease_query: str, limit: int = 50) -> dict:
    """Find all drugs for a disease/indication."""
    return await chembl_find_drugs_by_indication_impl(disease_query, limit)

@unified_mcp.tool(name="chembl_get_drug_indications")
async def chembl_get_drug_indications(molecule_chembl_id: str) -> dict:
    """Get all indications (diseases) for a specific drug."""
    return await chembl_get_drug_indications_impl(molecule_chembl_id)

# Register all CTG tools
@unified_mcp.tool(name="ctg_search_studies")
async def ctg_search_studies(
    condition: str = None,
    intervention: str = None,
    status: str = None,
    page_size: int = 20,
) -> dict:
    """Search clinical trials from ClinicalTrials.gov."""
    return await ctg_search_studies_impl(condition, intervention, status, page_size)

@unified_mcp.tool(name="ctg_get_study")
async def ctg_get_study(nct_id: str) -> dict:
    """Get single clinical trial study by NCT ID."""
    return await ctg_get_study_impl(nct_id)

@unified_mcp.tool(name="ctg_search_by_condition")
async def ctg_search_by_condition(
    condition_query: str, status: str = None, page_size: int = 20
) -> dict:
    """Search clinical trials by condition/disease."""
    return await ctg_search_by_condition_impl(condition_query, status, page_size)

@unified_mcp.tool(name="ctg_search_by_intervention")
async def ctg_search_by_intervention(
    intervention_query: str, status: str = None, page_size: int = 20
) -> dict:
    """Search clinical trials by intervention/treatment."""
    return await ctg_search_by_intervention_impl(intervention_query, status, page_size)

@unified_mcp.tool(name="ctg_get_study_metadata")
async def ctg_get_study_metadata() -> dict:
    """Get ClinicalTrials.gov data model metadata (available fields)."""
    return await ctg_get_study_metadata_impl()

