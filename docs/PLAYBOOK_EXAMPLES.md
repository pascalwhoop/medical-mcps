# Playbook Usage Examples

## Example 1: Drug-Centric Discovery for Ocrelizumab

**Goal**: Find new indications for ocrelizumab beyond MS

**Playbook**: `drug_centric`

### Step 1: Get Drug Profile

```python
# Tool: chembl_search_molecules
{
    "name": "chembl_search_molecules",
    "arguments": {
        "query": "ocrelizumab"
    }
}

# Tool: chembl_get_molecule
{
    "name": "chembl_get_molecule",
    "arguments": {
        "molecule_chembl_id": "CHEMBL2108041"
    }
}

# Tool: chembl_get_activities (CRITICAL - get ALL activities)
{
    "name": "chembl_get_activities",
    "arguments": {
        "molecule_chembl_id": "CHEMBL2108041"
    }
}
```

**Findings**:

- Primary target: CD20 (B cell depletion)
- Approved for: MS, rheumatoid arthritis
- Secondary effects: May affect B cell-mediated autoimmunity more broadly

### Step 2: Identify Secondary Effects

**Analysis**: Ocrelizumab depletes CD20+ B cells. B cells are involved in:

- Autoimmune diseases (SLE, Sjögren's, myasthenia gravis)
- B cell lymphomas
- Antibody-mediated rejection (transplant)

### Step 3: Map Targets to Pathways

```python
# Tool: reactome_query_pathways
{
    "name": "reactome_query_pathways",
    "arguments": {
        "query": "CD20 B cell"
    }
}

# Tool: kegg_find_pathways
{
    "name": "kegg_find_pathways",
    "arguments": {
        "query": "B cell activation"
    }
}
```

**Findings**: CD20 is involved in:

- B cell receptor signaling
- B cell activation pathways
- Autoimmune disease pathways

### Step 4: Find Disease-Pathway Overlap

```python
# Tool: reactome_get_disease_pathways
{
    "name": "reactome_get_disease_pathways",
    "arguments": {
        "disease_name": "systemic lupus erythematosus"
    }
}
```

**Findings**: SLE involves B cell dysregulation - potential overlap with CD20 targeting.

### Step 5: Generate Hypothesis

**Hypothesis**: "Ocrelizumab's CD20-mediated B cell depletion could reduce autoantibody production
in SLE, addressing a key pathophysiological mechanism."

### Step 6: Validate Against Evidence

```python
# Tool: ctg_search_studies
{
    "name": "ctg_search_studies",
    "arguments": {
        "condition": "systemic lupus erythematosus",
        "intervention": "ocrelizumab"
    }
}

# Tool: pubmed_search_articles
{
    "name": "pubmed_search_articles",
    "arguments": {
        "keywords": ["ocrelizumab", "SLE", "systemic lupus"]
    }
}
```

**Result**: Ocrelizumab is indeed being trialed for SLE - playbook successfully identified a real
repurposing opportunity!

---

## Example 2: Disease-Centric Discovery for Multiple Sclerosis

**Goal**: Find repurposable drugs for MS

**Playbook**: `disease_centric`

### Step 1: Map Disease Pathophysiology

```python
# Tool: reactome_get_disease_pathways
{
    "name": "reactome_get_disease_pathways",
    "arguments": {
        "disease_name": "multiple sclerosis"
    }
}

# Tool: kegg_get_disease
{
    "name": "kegg_get_disease",
    "arguments": {
        "disease_id": "H01490"  # MS KEGG ID
    }
}

# Tool: gwas_search_associations
{
    "name": "gwas_search_associations",
    "arguments": {
        "efo_id": "EFO_0003885"  # MS EFO ID
    }
}
```

**Findings**:

- Key pathways: Th17 differentiation, B cell activation, T cell receptor signaling
- GWAS genes: IL23R, HLA-DRB1, CD40, CD28

### Step 2: Prioritize Pathways by GWAS

**Analysis**: Th17 pathway has IL23R GWAS gene → High priority

### Step 3: Identify Druggable Targets

```python
# Tool: reactome_get_pathway_participants
{
    "name": "reactome_get_pathway_participants",
    "arguments": {
        "pathway_id": "R-HSA-6783783"  # Th17 differentiation
    }
}
```

**Findings**: IL-23, IL-17, RORγt, STAT3 are druggable targets

### Step 4: Find Drugs Targeting Pathways

```python
# Tool: chembl_get_activities_by_target
{
    "name": "chembl_get_activities_by_target",
    "arguments": {
        "target_chembl_id": "CHEMBL4204"  # IL-23
    }
}
```

**Findings**: Risankizumab (IL-23 inhibitor) approved for psoriasis

### Step 5: Evaluate Mechanistic Fit

**Analysis**:

- ✅ IL-23 is in Th17 pathway (MS-relevant)
- ✅ IL23R is GWAS-identified MS risk gene
- ✅ Risankizumab blocks Th17 differentiation
- ✅ Approved for similar autoimmune disease (psoriasis)

**Mechanistic Fit**: High - addresses root cause (Th17 dysregulation)

### Step 6: Check Unmet Needs

```python
# Tool: ctg_search_studies
{
    "name": "ctg_search_studies",
    "arguments": {
        "condition": "multiple sclerosis",
        "intervention": "risankizumab"
    }
}
```

**Result**: Risankizumab is being trialed for MS - playbook identified a real candidate!

---

## Example 3: Pathway-Centric Discovery

**Goal**: Find drugs for Th17 pathway dysregulation

**Playbook**: `pathway_centric`

### Step 1: Identify Disease Pathways

```python
# Tool: kegg_get_pathway
{
    "name": "kegg_get_pathway",
    "arguments": {
        "pathway_id": "hsa04659"  # Th17 cell differentiation
    }
}
```

### Step 2: Prioritize by GWAS

```python
# Tool: gwas_search_associations
{
    "name": "gwas_search_associations",
    "arguments": {
        "gene": "IL23R"
    }
}
```

**Finding**: IL23R is GWAS-validated → Pathway is high priority

### Step 3: Map Pathway Components

**Components**: IL-23, IL-17, RORγt, STAT3, IL-6, IL-1β

### Step 4: Find Drugs Modulating Pathway

```python
# For each component, find drugs
# Tool: chembl_get_activities_by_target
{
    "name": "chembl_get_activities_by_target",
    "arguments": {
        "target_chembl_id": "CHEMBL4204"  # IL-23
    }
}
```

**Findings**:

- Risankizumab (IL-23 inhibitor)
- Izokibep (IL-17A inhibitor)
- Siltuximab (IL-6 inhibitor)
- Filgotinib (JAK inhibitor → blocks STAT3)

### Step 5: Evaluate Pathway Restoration

**Analysis**:

- Does blocking IL-23 restore Th17 homeostasis? → Yes, reduces Th17 differentiation
- Does blocking IL-17 reduce Th17 effector function? → Yes
- Does blocking STAT3 reduce Th17 development? → Yes

**Result**: Multiple pathway-modulating drugs identified

---

## Example 4: Convergence Analysis

**Goal**: Identify high-confidence candidates by running multiple playbooks

### Run Multiple Playbooks

1. **Disease-Centric**: Identifies Risankizumab (IL-23 inhibitor)
2. **Pathway-Centric**: Identifies Risankizumab, Izokibep, Siltuximab
3. **Genetic-Centric**: Identifies Risankizumab (IL23R GWAS gene)

### Convergence Analysis

**Risankizumab** appears in all three playbooks:

- ✅ Disease-centric: Targets MS-relevant pathway
- ✅ Pathway-centric: Modulates Th17 pathway
- ✅ Genetic-centric: Targets GWAS-validated gene (IL23R)

**Confidence**: Very High - identified by multiple independent strategies

**Izokibep** appears in pathway-centric:

- ✅ Pathway-centric: Blocks IL-17 (Th17 effector cytokine)
- ⚠️ Not identified by disease/genetic playbooks

**Confidence**: Medium - single strategy identification

---

## Example 5: Phenotypic-Centric Discovery

**Goal**: Find drugs that reduce neuroinflammation (phenotype-first approach)

**Playbook**: `phenotypic_centric`

### Step 1: Define Target Phenotype

**Phenotype**: "Reduce microglial activation and neuroinflammation"

### Step 2: Find Drugs Producing Phenotype

```python
# Tool: pubmed_search_articles
{
    "name": "pubmed_search_articles",
    "arguments": {
        "keywords": ["microglial activation", "neuroinflammation", "drug"]
    }
}
```

**Findings**:

- Minocycline (antibiotic with anti-inflammatory effects)
- Fingolimod (S1P modulator - approved for MS)
- Metformin (antidiabetic - reduces neuroinflammation)

### Step 3: Deconvolute Mechanisms

```python
# Tool: chembl_get_activities
{
    "name": "chembl_get_activities",
    "arguments": {
        "molecule_chembl_id": "CHEMBL1431"  # Minocycline
    }
}
```

**Mechanisms**:

- Minocycline: Inhibits microglial activation, reduces pro-inflammatory cytokines
- Metformin: AMPK activation, reduces neuroinflammation via metabolic pathways

### Step 4: Validate Phenotype-Disease Link

**Analysis**: Neuroinflammation is central to MS pathophysiology → Reducing it should benefit MS

**Result**: Phenotypic approach identified drugs that might be missed by target-based approaches!

---

## Example 6: Individualized Discovery (David Fajgenbaum Case)

**Goal**: Identify underlying dysfunction from individual symptoms and find targeted treatment

**Playbook**: `individualized_centric`

**Background**: David Fajgenbaum was diagnosed with Castleman disease but identified mTOR
overactivation as the actual dysfunction, leading to successful treatment with sirolimus.

### Step 1: Document Comprehensive Phenotype

**Symptoms**:

- Recurrent fevers
- Enlarged lymph nodes
- Fatigue
- Weight loss
- Elevated inflammatory markers (IL-6, CRP)
- Organ dysfunction during flares

**Lab Values**:

- Elevated IL-6
- Elevated CRP
- Hypergammaglobulinemia
- Anemia
- Thrombocytopenia

**Clinical History**:

- Multiple relapses despite standard treatments
- Response to IL-6 blockade (siltuximab) but incomplete
- Pattern suggests pathway overactivation

### Step 2: Generate Differential Diagnosis

```python
# Tool: omim_search_entries
{
    "name": "omim_search_entries",
    "arguments": {
        "query": "Castleman disease"
    }
}

# Tool: mydisease_search_disease
{
    "name": "mydisease_search_disease",
    "arguments": {
        "query": "multicentric Castleman disease"
    }
}
```

**Differential**:

- Castleman disease (idiopathic multicentric)
- Autoimmune lymphoproliferative syndrome
- POEMS syndrome
- Other lymphoproliferative disorders

### Step 3: Systematically Rule Out Diseases

**Analysis**:

- Castleman disease: ✅ Matches phenotype, but mechanism unclear
- Other diseases: ❌ Don't match completely

**Key Insight**: Disease label "Castleman disease" doesn't explain WHY - need to find the
dysfunction.

### Step 4: Identify Underlying Dysfunction

```python
# Tool: reactome_get_disease_pathways
{
    "name": "reactome_get_disease_pathways",
    "arguments": {
        "disease_name": "Castleman disease"
    }
}

# Tool: kegg_get_disease
{
    "name": "kegg_get_disease",
    "arguments": {
        "disease_id": "H01490"  # Or search for Castleman
    }
}

# Tool: pubmed_search_articles
{
    "name": "pubmed_search_articles",
    "arguments": {
        "keywords": ["Castleman disease", "mTOR", "pathway"]
    }
}
```

**Finding**: Literature suggests mTOR pathway involvement in Castleman disease. mTOR overactivation
could explain:

- IL-6 overproduction
- Lymphoproliferation
- Inflammatory cascade

**Dysfunction Identified**: **mTOR pathway overactivation** (not "Castleman disease")

### Step 5: Determine Diagnostic Tests Needed

**Tests to Confirm**:

- Phospho-S6RP (downstream mTOR marker)
- Phospho-AKT (mTOR pathway activation)
- mTOR pathway gene expression
- Functional mTOR pathway assay

**Evidence Gaps**: Need to confirm mTOR overactivation directly

### Step 6: Find Drugs Targeting Dysfunction

```python
# Tool: chembl_get_activities_by_target
{
    "name": "chembl_get_activities_by_target",
    "arguments": {
        "target_chembl_id": "CHEMBL2095172"  # mTOR
    }
}

# Tool: chembl_search_molecules
{
    "name": "chembl_search_molecules",
    "arguments": {
        "query": "mTOR inhibitor"
    }
}
```

**Findings**:

- **Sirolimus** (rapamycin): mTOR inhibitor, approved for organ rejection
- **Everolimus**: mTOR inhibitor
- **Temsirolimus**: mTOR inhibitor

**Key**: Search for "mTOR inhibitors", not "Castleman disease drugs"

### Step 7: Evaluate Drug-Dysfunction Alignment

**Analysis**:

- ✅ Sirolimus directly inhibits mTOR
- ✅ Mechanism correct: inhibitor for overactivation
- ✅ Approved drug with known safety profile
- ✅ Used in similar immune dysregulation contexts

**Alignment**: Perfect - drug directly addresses identified dysfunction

### Step 8: Check Safety and Feasibility

```python
# Tool: openfda_label_searcher
{
    "name": "openfda_label_searcher",
    "arguments": {
        "name": "sirolimus"
    }
}
```

**Safety Profile**:

- Known side effects manageable
- Requires monitoring (immunosuppression)
- Risk-benefit favorable given life-threatening disease

### Step 9: Generate Treatment Hypothesis

**Hypothesis**: "Sirolimus will inhibit mTOR pathway overactivation, reducing IL-6 production and
lymphoproliferation, leading to resolution of fevers, lymphadenopathy, and inflammatory markers."

**Expected Outcomes**:

- Reduction in IL-6 levels
- Resolution of lymphadenopathy
- Normalization of inflammatory markers
- Prevention of relapses

**Monitoring Plan**:

- mTOR pathway markers (phospho-S6RP)
- IL-6 levels
- Clinical symptoms
- Drug levels

**Result**: David Fajgenbaum achieved long-term remission with sirolimus, confirming that targeting
the dysfunction (mTOR overactivation) was more effective than targeting the disease label (Castleman
disease).

---

## Best Practices Demonstrated

1. **Use ALL activities**: Don't just look at primary mechanism (Example 1)
2. **Prioritize GWAS validation**: Genetic evidence strengthens confidence (Example 2)
3. **Think pathways, not targets**: Diseases are pathway dysregulations (Example 3)
4. **Run multiple playbooks**: Convergence increases confidence (Example 4)
5. **Consider phenotypes**: Mechanism-agnostic approaches avoid bias (Example 5)
6. **Focus on dysfunction, not labels**: Disease labels are descriptions, not explanations
   (Example 6)
