# Every Cure Matrix Knowledge Graph Server

This server provides access to the Every Cure Matrix Knowledge Graph, a Neo4j-based knowledge graph
containing biomedical data for drug repurposing research.

## Server Details

-   **Name:** `everycure-matrix-kg-server`
-   **Path:** `/tools/everycure-kg/mcp`
-   **Base URL:** `http://localhost:8000/tools/everycure-kg/mcp` (default)
-   **Production URL:** `https://medical-mcps-production.up.railway.app/tools/everycure-kg/mcp`

## Database Versions

The server supports multiple database versions. Default is `everycure-v0.13.0` (latest). Available
versions include:

-   `everycure-v0.13.0` (latest)
-   `everycure-v0.12.0`
-   `everycure-v0.11.0`
-   `everycure-v0.10.0`
-   `everycure-0.4.8`
-   And more...

## Important Notes

-   **Read-only access:** This is a readonly connection. Only SELECT/READ queries are allowed. Write
    operations (CREATE, UPDATE, DELETE, MERGE) will fail.
-   **Node IDs:** Nodes are identified by their `id` property (e.g., `"MONDO:0007113"` for diseases,
    `"CHEMBL123"` for drugs).
-   **Biolink Model:** The graph uses Biolink Model node labels and relationship types (e.g.,
    `biolink:Drug`, `biolink:Disease`, `treats`, `associated_with`).

## Tools

### 1. `everycure_kg_execute_cypher`

Execute a Cypher query against the Every Cure Matrix Knowledge Graph.

-   **Parameters:**

    -   `query` (string, required): Cypher query string (e.g., `'MATCH (n:Gene) RETURN n LIMIT 10'`)
    -   `parameters` (dict, optional): Optional query parameters as a dictionary (e.g.,
        `{'name': 'CD20'}`)
    -   `database` (string, optional): Database version to query (defaults to latest:
        `everycure-v0.13.0`)

-   **Returns:** JSON with query results including records and metadata

-   **Example:**
    ```json
    {
        "query": "MATCH (d:Drug)-[:treats]->(dis:Disease {id: $disease_id}) RETURN d LIMIT 10",
        "parameters": { "disease_id": "MONDO:0007113" },
        "database": "everycure-v0.13.0"
    }
    ```

### 2. `everycure_kg_get_schema`

Get the database schema including node labels, relationship types, and property keys.

-   **Parameters:**

    -   `database` (string, optional): Database version to query (defaults to latest:
        `everycure-v0.13.0`)

-   **Returns:** JSON with schema information including:
    -   `labels`: List of all node labels in the database
    -   `relationship_types`: List of all relationship types
    -   `property_keys`: List of all property keys used in the database

### 3. `everycure_kg_get_stats`

Get database statistics including node count and relationship count.

-   **Parameters:**

    -   `database` (string, optional): Database version to query (defaults to latest:
        `everycure-v0.13.0`)

-   **Returns:** JSON with statistics including:
    -   `node_count`: Total number of nodes in the database
    -   `relationship_count`: Total number of relationships in the database

### 4. `everycure_kg_get_supported_types`

Get lists of supported node types and relationship types.

Returns both full lists from the database and curated "common" lists filtered for meaningful
biomedical pathway discovery. The "common" lists exclude ontology noise, procedures, and other
non-meaningful entities, focusing on types useful for drug repurposing and pathway analysis.

-   **Parameters:**

    -   `database` (string, optional): Database version to query (defaults to latest:
        `everycure-v0.13.0`)

-   **Returns:** Dict with:

    -   `node_types`: List of all node labels in the database (with biolink: prefix)
    -   `relationship_types`: List of all relationship types in the database
    -   `common_node_types`: Filtered list of meaningful node types (25 types)
    -   `common_relationship_types`: Filtered list of meaningful relationship types (29 types)
    -   `total_node_types`: Count of all node types
    -   `total_relationship_types`: Count of all relationship types

-   **Common node types include:** Drug, Disease, Gene, Protein, Pathway, PhenotypicFeature,
    ChemicalEntity, AnatomicalEntity, Cell, OrganismTaxon, etc.

-   **Common relationship types include:** treats, causes, associated_with, regulates,
    interacts_with, directly_physically_interacts_with, has_side_effect, contraindicated_in, etc.

### 5. `everycure_kg_get_neighborhood`

Get neighborhood of a node with optional filtering.

Returns neighbors connected to the specified node, optionally filtered by relationship types and
neighbor node labels.

-   **Parameters:**

    -   `node_id` (string, required): Node identifier (e.g., `"MONDO:0007113"`)
    -   `relationship_types` (list[string], optional): Filter by relationship types (e.g.,
        `["treats", "causes"]`)
    -   `node_labels` (list[string], optional): Filter neighbors by labels (e.g.,
        `["Drug", "Disease"]`)
    -   `max_hops` (integer, optional): Maximum distance from source node (1 = direct neighbors
        only, default: 1)
    -   `limit` (integer, optional): Maximum number of results to return (default: 100)
    -   `database` (string, optional): Database version (defaults to latest: `everycure-v0.13.0`)

-   **Returns:** Dict with neighbors and their relationships, including:
    -   `neighbors`: List of neighbor nodes with their properties
    -   `relationships`: List of relationships connecting to neighbors
    -   `source_node`: The source node information

### 6. `everycure_kg_get_neighborhood_stats`

Get neighborhood statistics (degree, relationship type distribution).

Returns statistical information about a node's neighborhood including total degree, relationship
type distribution, and neighbor label distribution.

-   **Parameters:**

    -   `node_id` (string, required): Node identifier (e.g., `"MONDO:0007113"`)
    -   `max_hops` (integer, optional): Maximum distance from source node (1 = direct neighbors
        only, default: 1)
    -   `database` (string, optional): Database version (defaults to latest: `everycure-v0.13.0`)

-   **Returns:** Dict with neighborhood statistics including:
    -   `neighbor_count`: Number of unique neighbors
    -   `relationship_count`: Total number of relationships
    -   `relationship_type_distribution`: Count of each relationship type
    -   `neighbor_label_distribution`: Count of each neighbor node label

### 7. `everycure_kg_get_weighted_neighborhood`

Get neighborhood sorted by evidence strength or other criteria.

Returns neighbors sorted by evidence strength (if available) or by relationship count/publication
count. This helps prioritize the most relevant connections.

-   **Parameters:**

    -   `node_id` (string, required): Node identifier (e.g., `"MONDO:0007113"`)
    -   `sort_by` (string, optional): Sort criterion (`"evidence_strength"`, `"publication_count"`,
        or `"relationship_count"`, default: `"evidence_strength"`)
    -   `relationship_types` (list[string], optional): Filter by relationship types
    -   `node_labels` (list[string], optional): Filter neighbors by labels
    -   `max_hops` (integer, optional): Maximum distance from source node (default: 1)
    -   `limit` (integer, optional): Maximum number of results (default: 100)
    -   `database` (string, optional): Database version (defaults to latest)

-   **Returns:** Dict with sorted neighbors and relationships

### 8. `everycure_kg_get_supported_metapaths`

Get list of supported metapaths for path finding.

Returns information about all available metapaths that can be used with `find_paths_by_metapath`.
These are biochemically sound patterns that prevent path explosion in the highly connected graph.

-   **Parameters:** None

-   **Returns:** Dict with:

    -   `metapaths`: List of metapath definitions (name, description, pattern, hops)
    -   `metapath_names`: List of metapath name strings for use with `find_paths_by_metapath`
    -   `total_metapaths`: Count of available metapaths

-   **Each metapath includes:**

    -   `name`: Human-readable name
    -   `description`: What the metapath represents
    -   `pattern`: List of node types and relationship types (e.g., `["Drug", "treats", "Disease"]`)
    -   `hops`: Number of hops in the path (1, 2, or 3)

-   **Note:** Custom metapaths are not supported in `find_paths_by_metapath`. Only these predefined
    metapaths can be used. To see what node types and relationship types exist in the database, use
    `get_supported_types()`.

### 9. `everycure_kg_find_paths_by_metapath`

Find paths between two nodes using a predefined metapath.

**IMPORTANT:** Only predefined metapaths are allowed to prevent path explosion in this highly
connected graph. Custom path patterns are not supported.

-   **Parameters:**

    -   `source_id` (string, required): Source node ID (e.g., `"CHEMBL123"` for a drug,
        `"MONDO:0007113"` for a disease)
    -   `target_id` (string, required): Target node ID (e.g., `"MONDO:0007113"` for a disease,
        `"HGNC:1100"` for a gene)
    -   `metapath_name` (string, required): Name of predefined metapath. Must be one of the
        metapaths returned by `get_supported_metapaths()`.
        -   Examples: `"drug_to_disease_direct"`, `"drug_to_disease_via_target"`
    -   `max_paths` (integer, optional): Maximum number of paths to return (default: 10)
    -   `database` (string, optional): Database version (defaults to latest: `everycure-v0.13.0`)

-   **Returns:** Dict with paths matching the metapath pattern, including:

    -   `paths`: List of path objects with nodes and relationships
    -   `metapath_info`: Information about the metapath used (name, description, pattern, hops)

-   **Available metapaths include:**

    -   `drug_to_disease_direct`: Drug -> treats -> Disease (1 hop)
    -   `drug_to_disease_via_target`: Drug -> interacts_with -> Protein -> associated_with ->
        Disease (2 hops)
    -   `drug_to_disease_via_pathway`: Drug -> interacts_with -> Protein -> part_of -> Pathway ->
        associated_with -> Disease (3 hops)
    -   `drug_to_disease_via_gene`: Drug -> interacts_with -> Protein -> gene_product_of -> Gene ->
        associated_with -> Disease (3 hops)
    -   `disease_to_disease_shared_gene`: Disease -> associated_with -> Gene -> associated_with ->
        Disease (2 hops)
    -   `drug_side_effect_path`: Drug -> causes -> PhenotypicFeature -> associated_with -> Disease
        (2 hops)

-   **Example:**
    ```json
    {
        "source_id": "CHEMBL123",
        "target_id": "MONDO:0007113",
        "metapath_name": "drug_to_disease_via_target"
    }
    ```

### 10. `everycure_kg_find_drugs_for_disease`

Find drugs for a disease using predefined metapaths.

Searches for drugs that treat or are associated with a disease using multiple metapaths. Can include
direct treatment relationships and/or indirect relationships via targets and pathways.

-   **Parameters:**

    -   `disease_id` (string, required): Disease identifier (e.g., `"MONDO:0007113"`)
    -   `include_indirect` (boolean, optional): If True, include indirect paths via targets/pathways
        (default: True)
    -   `exclude_contraindicated` (boolean, optional): If True, exclude drugs contraindicated for
        this disease (default: True)
    -   `max_paths_per_metapath` (integer, optional): Maximum paths to return per metapath
        (default: 10)
    -   `database` (string, optional): Database version (defaults to latest)

-   **Returns:** Dict with drugs found via different metapaths:
    -   `disease_id`: The disease ID queried
    -   `drugs`: List of drugs found, each with:
        -   `drug_id`: Drug identifier
        -   `drug_name`: Drug name
        -   `path_type`: Type of path (`"direct"` or `"via_target"`)
        -   `metapath`: Metapath used to find the drug
    -   `total_drugs`: Total number of unique drugs found

### 11. `everycure_kg_find_diseases_for_drug`

Find diseases associated with a drug using metapaths.

Searches for diseases that are indications, contraindications, or adverse events for a given drug.

-   **Parameters:**

    -   `drug_id` (string, required): Drug identifier (e.g., `"CHEMBL123"` or `"UMLS:C0017302"`)
    -   `include_indications` (boolean, optional): Include diseases the drug treats (default: True)
    -   `include_contraindications` (boolean, optional): Include diseases where drug is
        contraindicated (default: True)
    -   `include_adverse_events` (boolean, optional): Include diseases caused by drug side effects
        (default: True)
    -   `database` (string, optional): Database version (defaults to latest)

-   **Returns:** Dict with diseases found, categorized by relationship type:
    -   `drug_id`: The drug ID queried
    -   `diseases`: Dict with three categories:
        -   `indications`: List of diseases the drug treats
        -   `contraindications`: List of diseases where drug is contraindicated
        -   `adverse_events`: List of diseases caused by drug side effects
    -   `total_diseases`: Total number of unique diseases found

### 12. `everycure_kg_find_paths_by_custom_metapath`

Find paths between two nodes using a custom metapath pattern.

Allows users to specify custom metapath patterns. All node types and relationship types are
validated against Biolink Model to ensure they exist before constructing the query.

**IMPORTANT:** For safety, `max_hops` is limited to 5 by default to prevent path explosion. Very
long paths may return millions of results.

-   **Parameters:**

    -   `source_id` (string, required): Source node ID (e.g., `"CHEMBL123"` for a drug)
    -   `target_id` (string, required): Target node ID (e.g., `"MONDO:0007113"` for a disease)
    -   `metapath_pattern` (string, required): Custom metapath string with format:
        `"NodeType->RelType->NodeType->RelType->NodeType"`
        -   Examples:
            -   `"Drug->treats->Disease"`
            -   `"Drug->directly_physically_interacts_with->Protein->associated_with->Disease"`
            -   `"Drug->directly_physically_interacts_with->Protein->gene_product_of->Gene->associated_with->Disease"`
    -   `max_paths` (integer, optional): Maximum number of paths to return (default: 10)
    -   `max_hops` (integer, optional): Maximum allowed hops for safety (default: 5, max: 5)
    -   `database` (string, optional): Database version (defaults to latest: `everycure-v0.13.0`)

-   **Returns:** Dict with paths matching the metapath pattern, including:
    -   `paths`: List of path objects with nodes and relationships
    -   `metapath_pattern`: The validated metapath pattern used
    -   `validated_pattern`: Validated node labels and relationship types

## Example Workflows

### Finding Drugs for a Disease

1. Use `everycure_kg_find_drugs_for_disease` with a disease ID:
    ```json
    {
        "disease_id": "MONDO:0007113",
        "include_indirect": true,
        "exclude_contraindicated": true
    }
    ```

### Exploring a Node's Neighborhood

1. Get neighborhood statistics:

    ```json
    {
        "node_id": "MONDO:0007113",
        "max_hops": 1
    }
    ```

2. Get detailed neighborhood:
    ```json
    {
        "node_id": "MONDO:0007113",
        "node_labels": ["Drug"],
        "relationship_types": ["treats"],
        "max_hops": 1,
        "limit": 50
    }
    ```

### Finding Paths Between Entities

1. First, get supported metapaths:

    ```json
    {}
    ```

2. Then find paths using a metapath:
    ```json
    {
        "source_id": "CHEMBL123",
        "target_id": "MONDO:0007113",
        "metapath_name": "drug_to_disease_via_target"
    }
    ```

## Configuration

The server requires the following environment variables:

-   `EVERYCURE_KG_PASSWORD` (required): Password for Neo4j database access
-   `EVERYCURE_KG_URI` (optional): Neo4j database URI (defaults to
    `neo4j+s://neo4j.dev.everycure.org:7687`)
-   `EVERYCURE_KG_USERNAME` (optional): Database username (defaults to `readonly`)
-   `EVERYCURE_KG_DEFAULT_DATABASE` (optional): Default database version (defaults to
    `everycure-v0.13.0`)
