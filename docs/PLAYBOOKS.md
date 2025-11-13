# Drug Repurposing Playbooks

## Overview

The Drug Repurposing Playbook system provides structured strategies for navigating biomedical data
to discover drug repurposing opportunities. Each playbook represents a different "data trail" or
navigation strategy, enabling agents to approach the problem from multiple angles and triangulate on
promising candidates.

## Philosophy: First Principles Reasoning

The playbooks are designed around **first principles reasoning** - deducing and reasoning logically
about dysfunction of the human body, not just parroting what everyone else is saying. Insights lie
where others aren't looking, not where everyone's already looking.

### Key Principles

1. **Mechanistic Understanding First**: Understand disease pathophysiology before looking for drugs
2. **Look Beyond Primary Mechanisms**: Secondary effects, off-target actions, and pleiotropic
   mechanisms are often repurposing opportunities
3. **Genetic Validation**: Prioritize pathways/targets with GWAS or genetic evidence
4. **Network Thinking**: Diseases are pathway dysregulations, not single-target problems
5. **Convergence Through Diversity**: Run multiple playbooks independently - candidates identified
   by multiple strategies have higher confidence

## Available Playbooks

### 1. Drug-Centric Discovery (`drug_centric`)

**Starting Point**: An existing drug

**Framework**: Reverse Pharmacology / Phenotypic Drug Discovery

**Strategy**: Start with a known biological effect and work backwards to understand mechanisms.
Focus on what the drug DOES rather than what it was DESIGNED to do.

**Key Steps**:

1. Get comprehensive drug profile (targets, mechanisms, ALL activities)
2. Identify secondary effects and off-target mechanisms
3. Map targets to pathways
4. Find disease-pathway overlap
5. Generate mechanistic hypothesis
6. Validate against evidence

**Critical**: Review ALL activities from ChEMBL, not just primary mechanism. Secondary/off-target
effects are often repurposing opportunities.

### 2. Disease-Centric Discovery (`disease_centric`)

**Starting Point**: A specific disease

**Framework**: Systems Biology / Network Medicine

**Strategy**: Understand disease as a network of dysregulated pathways, then identify intervention
points. Focus on root causes, not just symptoms.

**Key Steps**:

1. Map disease pathophysiology comprehensively
2. Prioritize pathways by GWAS validation
3. Identify druggable targets
4. Find drugs targeting pathways
5. Evaluate mechanistic fit
6. Check unmet needs

**Critical**: Prioritize pathways with GWAS-identified risk genes. Genetic validation strengthens
pathway importance.

### 3. Target-Centric Discovery (`target_centric`)

**Starting Point**: A specific biological target

**Framework**: Target-Based Drug Discovery

**Strategy**: Focus on validated targets with strong disease association. Then find existing drugs
that modulate these targets.

**Key Steps**:

1. Validate target-disease association (GWAS, functional, clinical)
2. Understand target function in disease
3. Find ALL drugs for target (approved, investigational)
4. Evaluate mechanism alignment
5. Check other indications

**Use Case**: When a target is strongly validated but no approved drugs exist for the disease.

### 4. Pathway-Centric Discovery (`pathway_centric`)

**Starting Point**: A disease-relevant pathway

**Framework**: Network Pharmacology / Systems Pharmacology

**Strategy**: Diseases arise from pathway dysregulation. Drugs that restore pathway homeostasis may
be therapeutic, even if they don't target the 'primary' disease gene.

**Key Steps**:

1. Identify disease pathways
2. Prioritize by GWAS validation
3. Map pathway components
4. Find drugs modulating pathway
5. Evaluate pathway restoration

**Critical**: Consider pathway network effects, not just individual targets. Evaluate pathway
restoration, not just target binding.

### 5. Genetic-Centric Discovery (`genetic_centric`)

**Starting Point**: Disease-associated genetic variants

**Framework**: Mendelian Randomization / Genetic Drug Discovery

**Strategy**: Genetic variants that cause disease reveal causal pathways. Drugs that mimic
protective variants or compensate for risk variants may be therapeutic.

**Key Steps**:

1. Identify disease risk variants (GWAS, rare variants, Mendelian genes)
2. Understand variant mechanism
3. Identify protective variants
4. Find drugs compensating for variants
5. Validate using Mendelian randomization

**Use Case**: Leveraging genetic evidence to identify causal pathways and compensatory mechanisms.

### 6. Phenotypic-Centric Discovery (`phenotypic_centric`)

**Starting Point**: A desired phenotypic outcome

**Framework**: Phenotypic Drug Discovery / Reverse Pharmacology

**Strategy**: Focus on WHAT you want to achieve (phenotype), not HOW (mechanism). Mechanism can be
discovered later. This avoids mechanism bias.

**Key Steps**:

1. Define target phenotype precisely
2. Find drugs producing phenotype
3. Deconvolute mechanisms (reverse pharmacology)
4. Validate phenotype-disease link

**Use Case**: When you know what biological outcome you want but mechanism is unknown.

### 7. Network-Centric Discovery (`network_centric`)

**Starting Point**: Disease network

**Framework**: Network Medicine / Systems Pharmacology

**Strategy**: Diseases are network perturbations. Drugs that restore network topology or dynamics
may be therapeutic. Focus on network-level effects.

**Key Steps**:

1. Construct disease network
2. Identify network dysregulation
3. Find drugs restoring network
4. Evaluate network effects

**Use Case**: Understanding disease as a network perturbation and finding network-level
interventions.

### 8. Individualized Discovery (`individualized_centric`)

**Starting Point**: Individual symptoms and clinical presentation

**Framework**: Phenotype-to-Mechanism Discovery / Patient-Led Research

**Strategy**: Disease labels are clinical phenotype descriptions, not mechanistic explanations.
Focus on identifying the actual dysfunction (pathway overactivation, protein misfolding, metabolic
derangement) rather than accepting disease labels. The cure addresses the dysfunction, not the
label.

**Key Steps**:

1. Document comprehensive phenotype (all symptoms, labs, history)
2. Generate broad differential diagnosis
3. Systematically rule out diseases that don't fit completely
4. Identify underlying dysfunction (mechanism, not label)
5. Determine diagnostic tests needed to confirm dysfunction
6. Find drugs targeting dysfunction (not disease label)
7. Evaluate drug-dysfunction alignment
8. Check safety and feasibility
9. Generate mechanistic treatment hypothesis

**Inspired By**: David Fajgenbaum identified mTOR overactivation behind his Castleman disease
diagnosis and repurposed sirolimus (mTOR inhibitor) to achieve remission.

**Critical**: Focus on WHAT is actually wrong mechanistically, not disease labels. Example: "mTOR
overactivation" not "Castleman disease".

## Using Playbooks

### List All Playbooks

```python
# MCP tool call
{
    "name": "playbook_list_all",
    "arguments": {}
}
```

### Get Playbook Details

```python
# MCP tool call
{
    "name": "playbook_get_details",
    "arguments": {
        "playbook_id": "drug_centric"
    }
}
```

### Get Playbook Steps

```python
# MCP tool call
{
    "name": "playbook_get_steps",
    "arguments": {
        "playbook_id": "disease_centric"
    }
}
```

### Execute a Playbook Step

```python
# MCP tool call
{
    "name": "playbook_execute_step",
    "arguments": {
        "playbook_id": "drug_centric",
        "step_id": "1_get_drug_profile",
        "inputs": {
            "drug_name": "ocrelizumab"
        }
    }
}
```

### Compare Strategies

```python
# MCP tool call
{
    "name": "playbook_compare_strategies",
    "arguments": {
        "starting_point": "disease",
        "disease": "multiple sclerosis"
    }
}
```

## Convergence Strategy

**Run multiple playbooks independently** and compare results. Candidates identified by multiple
playbooks have higher confidence.

### Example Workflow

1. **Start with disease**: Run `disease_centric` playbook
2. **Start with pathways**: Run `pathway_centric` playbook
3. **Start with genetics**: Run `genetic_centric` playbook
4. **Compare results**: Drugs appearing in multiple playbooks are high-confidence candidates

### Convergence Criteria

A candidate has high confidence if:

- Identified by 2+ independent playbooks
- Has mechanistic hypothesis from multiple angles
- Has genetic/pathway validation
- Has evidence from literature/trials

## First Principles Frameworks

Each playbook is grounded in established academic frameworks:

1. **Reverse Pharmacology**: Start with phenotype/effect, discover mechanism
2. **Systems Biology**: Understand disease as network dysregulation
3. **Network Medicine**: Focus on network-level interventions
4. **Mendelian Randomization**: Use genetic variants to identify causal pathways
5. **Phenotypic Drug Discovery**: Avoid mechanism bias by focusing on outcomes

## Best Practices

1. **Be Conservative**: When uncertain, prefer inclusion over exclusion
2. **Look Beyond Primary**: Secondary effects and off-target mechanisms matter
3. **Validate Mechanistically**: Generate testable hypotheses connecting drug to disease
4. **Use Multiple Sources**: Cross-validate findings across databases and literature
5. **Think Networks**: Consider pathway and network effects, not just single targets
6. **Prioritize Genetic Evidence**: GWAS-validated pathways have stronger support

## Integration with Other Tools

Playbooks integrate with all available biomedical APIs:

- **ChEMBL**: Drug targets, mechanisms, activities
- **Reactome/KEGG/Pathway Commons**: Pathway analysis
- **GWAS Catalog**: Genetic validation
- **UniProt**: Protein information
- **PubMed**: Literature evidence
- **ClinicalTrials.gov**: Clinical evidence
- **OMIM**: Genetic disease information
- **MyGene/MyDisease/MyChem**: Gene/disease/drug information

## Example: Multiple Sclerosis Drug Repurposing

### Using Disease-Centric Playbook

1. **Map MS pathophysiology**: Th17 pathway, B cell activation, neuroinflammation
2. **Prioritize pathways**: Th17 (IL23R GWAS gene), B cell pathways (CD20 targets)
3. **Find druggable targets**: IL-23, IL-17, CD20, JAKs
4. **Find drugs**: Risankizumab (IL-23), Ocrelizumab (CD20), JAK inhibitors
5. **Evaluate fit**: IL-23 inhibitors align with Th17 dysregulation
6. **Check unmet needs**: Progressive MS, neuroprotection

### Using Pathway-Centric Playbook

1. **Identify MS pathways**: Th17 differentiation (KEGG hsa04659)
2. **GWAS validation**: IL23R is GWAS-identified MS risk gene
3. **Map components**: IL-23, IL-17, RORγt, STAT3
4. **Find pathway drugs**: Risankizumab (IL-23), Izokibep (IL-17)
5. **Evaluate restoration**: Does blocking IL-23 restore Th17 homeostasis?

### Convergence

Both playbooks identify **Risankizumab** (IL-23 inhibitor) as a candidate:

- ✅ Pathway validation (Th17 pathway)
- ✅ Genetic validation (IL23R GWAS gene)
- ✅ Mechanistic fit (blocks Th17 differentiation)
- ✅ Approved for similar disease (psoriasis)
- ✅ High confidence (identified by multiple strategies)

## Future Enhancements

- **Automated Playbook Execution**: Agents can execute playbooks end-to-end
- **Convergence Analysis**: Automatic comparison of results from multiple playbooks
- **Confidence Scoring**: Quantitative confidence scores based on evidence strength
- **Custom Playbooks**: User-defined playbooks for specific use cases
- **Playbook Templates**: Pre-built templates for common scenarios
