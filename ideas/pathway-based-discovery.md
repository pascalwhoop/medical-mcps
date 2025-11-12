# Pathway-Based Drug Discovery Ideas

This document captures ideas for using pathway analysis APIs (KEGG, Reactome, Pathway Commons) to
identify drug repurposing opportunities.

## Core Concept

**Pathway-based discovery** identifies drugs by analyzing their targets' involvement in
disease-relevant pathways, rather than just looking at primary indications.

### Why Pathways Matter

1. **Disease mechanisms are pathway-based** - Diseases involve dysregulated pathways, not single
   targets
2. **Drugs often affect multiple pathways** - Through primary and secondary targets
3. **Pathway overlap reveals opportunities** - Drugs approved for one disease may affect pathways
   relevant to another
4. **GWAS validation** - Genetic variants in pathway genes validate pathway importance

## Workflow Pattern

### Step 1: Identify Disease-Relevant Pathways

**Using KEGG:**

```python
# Find disease entry
diseases = kegg_find_diseases("multiple sclerosis")
disease_info = kegg_get_disease("H01490")  # MS disease ID

# Extract associated pathways
pathways = disease_info["pathways"]  # e.g., Th1/Th2, Th17, TCR signaling

# Get pathway details
for pathway_id in pathways:
    pathway_info = kegg_get_pathway_info(pathway_id)
    # Analyze genes, drugs, and interactions
```

**Using Reactome:**

```python
# Query pathways related to disease
pathways = reactome_query_pathways("T cell activation")
disease_pathways = reactome_get_disease_pathways("multiple sclerosis")
```

**Using Pathway Commons:**

```python
# Search pathways by disease or process
pathways = pathwaycommons_search("multiple sclerosis")
```

### Step 2: Map GWAS Risk Genes to Pathways

**Using GWAS Catalog:**

```python
# Get disease genetic associations
associations = gwas_search_associations(efo_id="EFO_0003885")  # MS EFO ID

# Extract risk genes
risk_genes = [assoc["gene"] for assoc in associations]

# Map to pathways
for gene in risk_genes:
    # Find pathways containing this gene
    gene_pathways = kegg_find_pathways_by_gene(gene)
    # Prioritize pathways with multiple risk genes
```

**Key Insight:** Pathways with multiple GWAS-identified risk genes are high-priority targets.

### Step 3: Identify Drugs Targeting Pathway Components

**Using KEGG:**

```python
# For each pathway, get associated drugs
pathway_info = kegg_get_pathway_info("hsa04659")  # Th17 pathway
drugs = pathway_info["drugs"]  # Drugs targeting pathway components

# Example: Th17 pathway drugs
# - Siltuximab (IL-6 inhibitor)
# - Risankizumab (IL-23 inhibitor)
# - Izokibep (IL-17A inhibitor)
```

**Using ChEMBL:**

```python
# For each pathway gene/target, find drugs
for target in pathway_targets:
    activities = chembl_get_activities_by_target(target)
    drugs = [act["molecule_chembl_id"] for act in activities]
```

### Step 4: Evaluate Drug-Pathway-Disease Alignment

**Criteria:**

1. **Pathway relevance** - Is the pathway dysregulated in the disease?
2. **Target druggability** - Are pathway components druggable?
3. **Drug availability** - Are approved drugs available?
4. **Safety profile** - Are drugs safe for chronic use?
5. **Mechanistic fit** - Does drug mechanism align with disease pathophysiology?

## Example: Multiple Sclerosis

### High-Priority Pathways

**1. Th17 Cell Differentiation (KEGG: hsa04659)**

**Key Components:**

- IL17A, IL17F (Th17 signature cytokines)
- IL23R (GWAS-identified MS risk gene)
- IL23A (Interleukin-23 alpha)
- RORC (RORγt transcription factor)
- STAT3 (Critical for Th17 differentiation)
- IL6, IL1B (Promote Th17 differentiation)

**Drugs Targeting This Pathway:**

- **Risankizumab** - IL-23p19 inhibitor (approved for psoriasis)
- **Izokibep** - IL-17A inhibitor (approved for psoriasis)
- **Siltuximab** - IL-6 inhibitor (approved for Castleman's disease)
- **Filgotinib** - JAK inhibitor (blocks STAT3 signaling)

**Repurposing Rationale:**

- Th17 cells are strongly implicated in MS pathogenesis
- IL-23R is a GWAS-identified MS risk gene
- IL-23/IL-17 inhibitors are approved for similar autoimmune diseases
- **Confidence: High**

**2. Th1/Th2 Cell Differentiation (KEGG: hsa04658)**

**Key Components:**

- HLA-DRB1, HLA-DQB1 (Strongest MS genetic risk factors)
- IFNG (Interferon-gamma - Th1 cytokine)
- STAT4, STAT6 (Transcription factors)
- JAK1, JAK2, JAK3 (Janus kinases)

**Drugs Targeting This Pathway:**

- **Filgotinib** - JAK1 inhibitor
- **Abrocitinib** - JAK1 inhibitor
- **Brepocitinib** - JAK1/TYK2 inhibitor
- **Deucravacitinib** - TYK2 inhibitor

**Repurposing Rationale:**

- JAK-STAT signaling is central to T cell differentiation
- Approved for other autoimmune diseases
- Some JAK inhibitors already in MS clinical trials
- **Confidence: High**

**3. T Cell Receptor Signaling (KEGG: hsa04660)**

**Key Components:**

- CD3 complex (TCR components)
- CD28 (Costimulatory receptor)
- CTLA4, PDCD1 (Checkpoint inhibitors - PDCD1 is MS-associated)
- NF-AT, NF-κB (Transcription factors)

**Drugs Targeting This Pathway:**

- **Tacrolimus** - Calcineurin/NF-AT inhibitor
- **Cyclosporine** - Calcineurin/NF-AT inhibitor
- **Ipilimumab** - CTLA-4 inhibitor (likely contraindicated)
- **Nivolumab** - PD-1 inhibitor (likely contraindicated)

**Repurposing Rationale:**

- NF-AT is critical for T cell activation
- Calcineurin inhibitors could reduce autoreactive T cell activation
- **Confidence: Medium** - Toxicity concerns limit long-term use

### Pathway Analysis Workflow

```python
# 1. Get disease pathways from KEGG
ms_disease = kegg_get_disease("H01490")
pathways = ms_disease["pathways"]

# 2. For each pathway, get detailed information
for pathway_id in pathways:
    pathway_info = kegg_get_pathway_info(pathway_id)

    # 3. Extract genes and drugs
    genes = pathway_info["genes"]
    drugs = pathway_info["drugs"]

    # 4. Check GWAS support
    gwas_associations = gwas_search_associations(efo_id="EFO_0003885")
    risk_genes = set([assoc["gene"] for assoc in gwas_associations])
    pathway_risk_genes = risk_genes.intersection(set(genes))

    # 5. Prioritize pathways with GWAS support
    if len(pathway_risk_genes) > 0:
        print(f"Pathway {pathway_id} has {len(pathway_risk_genes)} GWAS risk genes")

        # 6. Evaluate drugs targeting this pathway
        for drug in drugs:
            drug_info = evaluate_drug_for_disease(drug, "multiple sclerosis")
            if drug_info["relevance"] == "high":
                print(f"  Candidate: {drug_info['name']}")
```

## Advanced Patterns

### Multi-Pathway Analysis

**Concept:** Drugs affecting multiple disease-relevant pathways may be more effective.

**Workflow:**

1. Identify all disease-relevant pathways
2. For each drug, count how many pathways it affects
3. Prioritize drugs with multi-pathway effects
4. Consider pathway interactions (synergistic vs. antagonistic)

### Pathway Enrichment Analysis

**Concept:** Compare drug targets to disease pathway genes to calculate enrichment.

**Workflow:**

1. Get disease pathway genes (from KEGG/Reactome)
2. Get drug targets (from ChEMBL)
3. Calculate overlap and statistical significance
4. Rank drugs by pathway enrichment score

### Pathway-Disease Similarity

**Concept:** Drugs approved for diseases with similar pathway dysregulation may be repurposable.

**Workflow:**

1. Identify pathways dysregulated in target disease
2. Find other diseases with similar pathway dysregulation
3. Identify drugs approved for those diseases
4. Evaluate repurposing potential

**Example:** Psoriasis and MS both involve Th17 pathway dysregulation. IL-23 inhibitors approved for
psoriasis are candidates for MS.

## API Integration Tips

### KEGG API

**Strengths:**

- Comprehensive pathway and drug data
- Disease-pathway associations
- Drug-pathway associations

**Limitations:**

- Rate limits
- Some pathways may not have drug associations

**Best Practices:**

- Cache pathway data (changes infrequently)
- Use disease IDs to find pathways efficiently
- Extract both genes and drugs from pathways

### Reactome API

**Strengths:**

- Detailed pathway hierarchies
- Disease-pathway associations
- Pathway interactions

**Limitations:**

- Less drug data than KEGG
- May require multiple queries to find disease pathways

**Best Practices:**

- Use query endpoints for flexible searching
- Explore pathway hierarchies for related pathways
- Combine with KEGG for comprehensive analysis

### Pathway Commons API

**Strengths:**

- Integrated data from multiple sources
- Pathway interactions and networks

**Limitations:**

- May have timeout issues with large queries
- Less structured than KEGG/Reactome

**Best Practices:**

- Use for pathway network analysis
- Combine with KEGG/Reactome for validation
- Handle timeouts gracefully

## Success Metrics

### Pathway-Based Discovery Success Indicators

1. **GWAS validation** - Pathways with GWAS-identified risk genes
2. **Drug availability** - Approved drugs targeting pathway components
3. **Mechanistic fit** - Drug mechanism aligns with pathway dysregulation
4. **Clinical evidence** - Drugs already in disease trials or used in similar diseases
5. **Safety profile** - Drugs with acceptable safety for chronic use

### Example Success Story

**Risankizumab (IL-23 inhibitor) for MS:**

- ✅ **Pathway:** Th17 differentiation (KEGG: hsa04659)
- ✅ **GWAS support:** IL23R is GWAS-identified MS risk gene
- ✅ **Drug availability:** Approved for psoriasis
- ✅ **Mechanistic fit:** Blocks Th17 differentiation, key in MS
- ✅ **Similar disease:** Approved for psoriasis (similar autoimmune mechanisms)
- ✅ **Safety:** Favorable safety profile

**Confidence: High** - Strong pathway, GWAS, and mechanistic support

## References

- KEGG Disease Database: H01490 (Multiple sclerosis)
- KEGG Pathways: hsa04658 (Th1/Th2), hsa04659 (Th17), hsa04660 (TCR signaling)
- Reactome: T cell activation pathways
- GWAS Catalog: Disease genetic associations

---

**Key Takeaway:** Pathway-based discovery leverages the fact that diseases are pathway
dysregulations, not single-target problems. By analyzing drug targets' involvement in
disease-relevant pathways, we can identify repurposing opportunities that might be missed by
target-only approaches.
