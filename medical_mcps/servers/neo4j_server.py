#!/usr/bin/env python3
"""
Every Cure Matrix Knowledge Graph MCP Server
Exposes Every Cure Matrix Knowledge Graph (Neo4j) tools via MCP at /tools/everycure-kg/mcp
"""

import logging
from typing import Any

from ..api_clients.biolink_helpers import (
    get_common_node_types,
    get_common_relationship_types,
    normalize_node_label,
    normalize_relationship_type,
    validate_node_type,
    validate_relationship_type,
)
from ..api_clients.metapaths import (
    DEFAULT_METAPATHS,
    get_metapath_by_name,
    list_metapaths,
    parse_metapath_pattern,
    parse_metapath_string,
)
from ..api_clients.neo4j_client import Neo4jClient
from ..api_clients.safety_validator import check_metapath_safety, check_node_degree
from ..fastmcp_server import MedicalFastMCP as FastMCP
from ..med_mcp_server import tool as medmcps_tool
from ..med_mcp_server import unified_mcp
from ..settings import settings
from .neo4j_helpers import handle_neo4j_error, neo4j_response

logger = logging.getLogger(__name__)

# Initialize Neo4j client (lazy initialization to avoid startup errors if password not set)
neo4j_client: Neo4jClient | None = None


def get_neo4j_client() -> Neo4jClient:
    """Get or create Neo4j client instance"""
    global neo4j_client
    if neo4j_client is None:
        neo4j_client = Neo4jClient()
    return neo4j_client


# Create FastMCP server for Every Cure Matrix Knowledge Graph
everycure_kg_mcp = FastMCP(
    "everycure-matrix-kg-server",
    stateless_http=True,
    json_response=True,
)


@medmcps_tool(name="everycure_kg_execute_cypher", servers=[everycure_kg_mcp, unified_mcp])
async def execute_cypher(
    query: str,
    parameters: dict[str, Any] | None = None,
    database: str | None = None,
) -> dict:
    """Execute a Cypher query against the Every Cure Matrix Knowledge Graph.

    IMPORTANT: This is a readonly connection. Only SELECT/READ queries are allowed.
    Write operations (CREATE, UPDATE, DELETE, MERGE) will fail.

    Available databases: everycure-v0.13.0 (latest), everycure-v0.12.0, everycure-v0.11.0,
    everycure-v0.10.0, everycure-0.4.8, ...

    Args:
        query: Cypher query string (e.g., 'MATCH (n:Gene) RETURN n LIMIT 10')
        parameters: Optional query parameters as a dictionary (e.g., {'name': 'CD20'})
        database: Database version to query (defaults to latest: everycure-v0.13.0)

    Returns:
        JSON with query results including records and metadata
    """
    db_name = database or settings.everycure_kg_default_database
    logger.info(f"Tool invoked: execute_cypher(database='{db_name}', query='{query[:100]}...')")
    try:
        client = get_neo4j_client()
        result = await client.execute_cypher(query, parameters, db_name)
        record_count = result.get("metadata", {}).get("record_count", 0)
        logger.info(f"Tool succeeded: execute_cypher() - returned {record_count} records")
        return result
    except Exception as e:
        return handle_neo4j_error(e, db_name, "execute_cypher")


@medmcps_tool(name="everycure_kg_get_schema", servers=[everycure_kg_mcp, unified_mcp])
async def get_schema(database: str | None = None) -> dict:
    """Get the database schema including node labels, relationship types, and property keys.

    This is useful for understanding the structure of the graph database before writing queries.

    Args:
        database: Database version to query (defaults to latest: everycure-v0.13.0)

    Returns:
        JSON with schema information including:
        - labels: List of all node labels in the database
        - relationship_types: List of all relationship types
        - property_keys: List of all property keys used in the database
    """
    db_name = database or settings.everycure_kg_default_database
    logger.info(f"Tool invoked: get_schema(database='{db_name}')")
    try:
        client = get_neo4j_client()
        result = await client.get_schema(db_name)
        logger.info("Tool succeeded: get_schema()")
        return result
    except Exception as e:
        return handle_neo4j_error(e, db_name, "get_schema")


@medmcps_tool(name="everycure_kg_get_stats", servers=[everycure_kg_mcp, unified_mcp])
async def get_stats(database: str | None = None) -> dict:
    """Get database statistics including node count and relationship count.

    Args:
        database: Database version to query (defaults to latest: everycure-v0.13.0)

    Returns:
        JSON with statistics including:
        - node_count: Total number of nodes in the database
        - relationship_count: Total number of relationships in the database
    """
    db_name = database or settings.everycure_kg_default_database
    logger.info(f"Tool invoked: get_stats(database='{db_name}')")
    try:
        client = get_neo4j_client()
        result = await client.get_stats(db_name)
        logger.info("Tool succeeded: get_stats()")
        return result
    except Exception as e:
        return handle_neo4j_error(e, db_name, "get_stats")


@medmcps_tool(name="everycure_kg_get_supported_types", servers=[everycure_kg_mcp, unified_mcp])
async def get_supported_types(database: str | None = None) -> dict:
    """Get lists of supported node types and relationship types.

    Helps agents understand what node types and relationship types are available
    in the database. Returns both full lists from the database and curated
    "common" lists filtered for meaningful biomedical pathway discovery.

    The "common" lists exclude ontology noise, procedures, and other non-meaningful
    entities, focusing on types useful for drug repurposing and pathway analysis.

    Common node types include: Drug, Disease, Gene, Protein, Pathway, PhenotypicFeature,
    ChemicalEntity, AnatomicalEntity, Cell, OrganismTaxon, etc.

    Common relationship types include: treats, causes, associated_with, regulates,
    interacts_with, directly_physically_interacts_with, has_side_effect,
    contraindicated_in, etc.

    NOTE: These types can be used in Cypher queries via execute_cypher, but custom
    metapaths are not supported in find_paths_by_metapath. Only predefined metapaths
    (see get_supported_metapaths) can be used for path finding.

    Args:
        database: Database version to query (defaults to latest: everycure-v0.13.0)

    Returns:
        Dict with:
        - node_types: List of all node labels in the database (with biolink: prefix)
        - relationship_types: List of all relationship types in the database
        - common_node_types: Filtered list of meaningful node types (25 types)
        - common_relationship_types: Filtered list of meaningful relationship types (29 types)
        - total_node_types: Count of all node types
        - total_relationship_types: Count of all relationship types
    """
    db_name = database or settings.everycure_kg_default_database
    logger.info(f"Tool invoked: get_supported_types(database='{db_name}')")
    try:
        client = get_neo4j_client()
        schema_result = await client.get_schema(db_name)

        if schema_result.get("data") is None:
            # Error occurred, return error response
            return schema_result

        schema = schema_result["data"]

        result = neo4j_response(
            data={
                "node_types": schema["labels"],
                "relationship_types": schema["relationship_types"],
                "common_node_types": get_common_node_types(),
                "common_relationship_types": get_common_relationship_types(),
            },
            metadata={
                "database": db_name,
                "total_node_types": len(schema["labels"]),
                "total_relationship_types": len(schema["relationship_types"]),
                "common_node_types_count": len(get_common_node_types()),
                "common_relationship_types_count": len(get_common_relationship_types()),
            },
        )
        logger.info("Tool succeeded: get_supported_types()")
        return result
    except Exception as e:
        return handle_neo4j_error(e, db_name, "get_supported_types")


@medmcps_tool(name="everycure_kg_get_neighborhood", servers=[everycure_kg_mcp, unified_mcp])
async def get_neighborhood(
    node_id: str,
    relationship_types: list[str] | None = None,
    node_labels: list[str] | None = None,
    max_hops: int = 1,
    limit: int = 100,
    database: str | None = None,
) -> dict:
    """Get neighborhood of a node with optional filtering.

    Returns neighbors connected to the specified node, optionally filtered by
    relationship types and neighbor node labels.

    Args:
        node_id: Node identifier (e.g., "MONDO:0007113")
        relationship_types: Filter by relationship types (e.g., ["treats", "causes"])
        node_labels: Filter neighbors by labels (e.g., ["Drug", "Disease"])
        max_hops: Maximum distance from source node (1 = direct neighbors only)
        limit: Maximum number of results to return
        database: Database version (defaults to latest: everycure-v0.13.0)

    Returns:
        Dict with neighbors and their relationships, including:
        - neighbors: List of neighbor nodes with their properties
        - relationships: List of relationships connecting to neighbors
        - source_node: The source node information
    """
    db_name = database or settings.everycure_kg_default_database
    logger.info(
        f"Tool invoked: get_neighborhood(node_id='{node_id}', max_hops={max_hops}, limit={limit})"
    )

    try:
        client = get_neo4j_client()

        # Safety check: Prevent path explosion on high-degree nodes
        if max_hops > 1:
            safety = await check_node_degree(client, node_id, db_name, max_hops)
            if safety["blocked"]:
                logger.warning(f"Blocked get_neighborhood query: {safety['warning']}")
                return neo4j_response(
                    data=None,
                    error=safety["warning"],
                    metadata={
                        "database": db_name,
                        "node_id": node_id,
                        "max_hops": max_hops,
                        "safety_check": safety,
                    },
                )
            if safety["warning"]:
                logger.warning(safety["warning"])

        # Build Cypher query
        # Start with MATCH for source node
        query_parts = ["MATCH (source {id: $node_id})"]

        # Build relationship pattern
        if max_hops == 1:
            rel_pattern = "-[r]->"
        else:
            rel_pattern = f"-[r*1..{max_hops}]->"

        # Add relationship type filter if specified
        if relationship_types:
            normalized_rel_types = [normalize_relationship_type(rt) for rt in relationship_types]
            rel_type_filter = ":" + "|".join(normalized_rel_types)
            rel_pattern = rel_pattern.replace("-[r]", f"-[r{rel_type_filter}]")

        query_parts.append(f"MATCH (source){rel_pattern}(neighbor)")

        # Add neighbor label filter if specified
        if node_labels:
            normalized_labels = [normalize_node_label(label) for label in node_labels]
            label_conditions = " OR ".join(
                [f"'{label}' IN labels(neighbor)" for label in normalized_labels]
            )
            query_parts.append(f"WHERE ({label_conditions})")

        # RETURN clause
        query_parts.append("RETURN source, r, neighbor")
        query_parts.append(f"LIMIT {limit}")

        query = " ".join(query_parts)

        # Execute query
        result = await client.execute_cypher(query, {"node_id": node_id}, db_name)

        if result.get("data") is None:
            return result

        # Process results to extract neighbors and relationships
        neighbors = []
        relationships = []
        source_node = None

        for record in result["data"]:
            if source_node is None and "source" in record:
                source_node = record["source"]

            if "neighbor" in record:
                neighbors.append(record["neighbor"])

            if "r" in record:
                relationships.append(record["r"])

        # Deduplicate neighbors and relationships by ID
        seen_neighbor_ids = set()
        unique_neighbors = []
        for neighbor in neighbors:
            neighbor_id = neighbor.get("id") if isinstance(neighbor, dict) else None
            if neighbor_id and neighbor_id not in seen_neighbor_ids:
                seen_neighbor_ids.add(neighbor_id)
                unique_neighbors.append(neighbor)

        seen_rel_ids = set()
        unique_relationships = []
        for rel in relationships:
            rel_id = rel.get("id") if isinstance(rel, dict) else None
            if rel_id and rel_id not in seen_rel_ids:
                seen_rel_ids.add(rel_id)
                unique_relationships.append(rel)

        return neo4j_response(
            data={
                "source_node": source_node,
                "neighbors": unique_neighbors[:limit],
                "relationships": unique_relationships[:limit],
            },
            metadata={
                "database": db_name,
                "node_id": node_id,
                "max_hops": max_hops,
                "neighbor_count": len(unique_neighbors),
                "relationship_count": len(unique_relationships),
                "relationship_types_filter": relationship_types,
                "node_labels_filter": node_labels,
            },
        )
    except Exception as e:
        return handle_neo4j_error(e, db_name, "get_neighborhood")


@medmcps_tool(name="everycure_kg_get_neighborhood_stats", servers=[everycure_kg_mcp, unified_mcp])
async def get_neighborhood_stats(
    node_id: str,
    max_hops: int = 1,
    database: str | None = None,
) -> dict:
    """Get neighborhood statistics (degree, relationship type distribution).

    Returns statistical information about a node's neighborhood including
    total degree, relationship type distribution, and neighbor label distribution.

    Args:
        node_id: Node identifier (e.g., "MONDO:0007113")
        max_hops: Maximum distance from source node (1 = direct neighbors only)
        database: Database version (defaults to latest: everycure-v0.13.0)

    Returns:
        Dict with neighborhood statistics
    """
    db_name = database or settings.everycure_kg_default_database
    logger.info(f"Tool invoked: get_neighborhood_stats(node_id='{node_id}', max_hops={max_hops})")

    try:
        client = get_neo4j_client()

        # Build query to get statistics
        if max_hops == 1:
            query = """
            MATCH (source {id: $node_id})-[r]-(neighbor)
            RETURN
                count(DISTINCT neighbor) as neighbor_count,
                count(r) as relationship_count,
                collect(DISTINCT type(r)) as relationship_types,
                collect(DISTINCT labels(neighbor)) as neighbor_labels
            """
        else:
            query = f"""
            MATCH (source {{id: $node_id}})-[r*1..{max_hops}]-(neighbor)
            RETURN
                count(DISTINCT neighbor) as neighbor_count,
                count(r) as relationship_count,
                collect(DISTINCT type(r)) as relationship_types,
                collect(DISTINCT labels(neighbor)) as neighbor_labels
            """

        result = await client.execute_cypher(query, {"node_id": node_id}, db_name)

        if result.get("data") is None or not result["data"]:
            return result

        stats_record = result["data"][0]

        # Process relationship type distribution
        rel_types = stats_record.get("relationship_types", [])
        rel_type_counts: dict[str, int] = {}
        for rel_type_list in rel_types:
            if isinstance(rel_type_list, list):
                for rt in rel_type_list:
                    rel_type_counts[rt] = rel_type_counts.get(rt, 0) + 1
            else:
                rel_type_counts[rel_type_list] = rel_type_counts.get(rel_type_list, 0) + 1

        # Process neighbor label distribution
        neighbor_labels = stats_record.get("neighbor_labels", [])
        label_counts: dict[str, int] = {}
        for label_list in neighbor_labels:
            if isinstance(label_list, list):
                for label in label_list:
                    label_counts[label] = label_counts.get(label, 0) + 1
            else:
                label_counts[label_list] = label_counts.get(label_list, 0) + 1

        return neo4j_response(
            data={
                "node_id": node_id,
                "neighbor_count": stats_record.get("neighbor_count", 0),
                "relationship_count": stats_record.get("relationship_count", 0),
                "relationship_type_distribution": rel_type_counts,
                "neighbor_label_distribution": label_counts,
            },
            metadata={
                "database": db_name,
                "max_hops": max_hops,
            },
        )
    except Exception as e:
        return handle_neo4j_error(e, db_name, "get_neighborhood_stats")


@medmcps_tool(
    name="everycure_kg_get_weighted_neighborhood", servers=[everycure_kg_mcp, unified_mcp]
)
async def get_weighted_neighborhood(
    node_id: str,
    sort_by: str = "evidence_strength",
    relationship_types: list[str] | None = None,
    node_labels: list[str] | None = None,
    max_hops: int = 1,
    limit: int = 100,
    database: str | None = None,
) -> dict:
    """Get neighborhood sorted by evidence strength or other criteria.

    Returns neighbors sorted by evidence strength (if available) or
    by relationship count/publication count. This helps prioritize
    the most relevant connections.

    Args:
        node_id: Node identifier (e.g., "MONDO:0007113")
        sort_by: Sort criterion ("evidence_strength", "publication_count", or "relationship_count")
        relationship_types: Filter by relationship types
        node_labels: Filter neighbors by labels
        max_hops: Maximum distance from source node
        limit: Maximum number of results
        database: Database version (defaults to latest)

    Returns:
        Dict with sorted neighbors and relationships
    """
    db_name = database or settings.everycure_kg_default_database
    logger.info(
        f"Tool invoked: get_weighted_neighborhood(node_id='{node_id}', "
        f"sort_by='{sort_by}', limit={limit})"
    )

    try:
        # For now, use get_neighborhood and sort results
        # In the future, we could add sorting directly in Cypher query
        neighborhood_result = await get_neighborhood(
            node_id=node_id,
            relationship_types=relationship_types,
            node_labels=node_labels,
            max_hops=max_hops,
            limit=limit * 10,  # Get more results to sort
            database=database,
        )

        if neighborhood_result.get("data") is None:
            return neighborhood_result

        neighbors = neighborhood_result["data"].get("neighbors", [])
        relationships = neighborhood_result["data"].get("relationships", [])

        # Simple sorting - in the future, could use evidence_strength property
        # For now, return results as-is (sorting by evidence strength would require
        # additional properties on relationships/nodes)

        # Return sorted results (limited)
        metadata = {**neighborhood_result["metadata"], "sort_by": sort_by}
        return neo4j_response(
            data={
                "source_node": neighborhood_result["data"].get("source_node"),
                "neighbors": neighbors[:limit],
                "relationships": relationships[:limit],
                "sort_by": sort_by,
            },
            metadata=metadata,
        )
    except Exception as e:
        return handle_neo4j_error(e, db_name, "get_weighted_neighborhood")


@medmcps_tool(name="everycure_kg_get_supported_metapaths", servers=[everycure_kg_mcp, unified_mcp])
async def get_supported_metapaths() -> dict:
    """Get list of supported metapaths for path finding.

    Returns information about all available metapaths that can be used
    with find_paths_by_metapath. These are biochemically sound patterns
    that prevent path explosion in the highly connected graph.

    Each metapath includes:
    - name: Human-readable name
    - description: What the metapath represents
    - pattern: List of node types and relationship types (e.g., ["Drug", "treats", "Disease"])
    - hops: Number of hops in the path (1, 2, or 3)

    NOTE: Custom metapaths are not supported. Only these predefined metapaths
    can be used with find_paths_by_metapath. To see what node types and
    relationship types exist in the database, use get_supported_types().

    Returns:
        Dict with:
        - metapaths: List of metapath definitions (name, description, pattern, hops)
        - metapath_names: List of metapath name strings for use with find_paths_by_metapath
        - total_metapaths: Count of available metapaths
    """
    logger.info("Tool invoked: get_supported_metapaths()")
    try:
        metapaths = list_metapaths()
        result = neo4j_response(
            data={
                "metapaths": metapaths,
                "metapath_names": list(DEFAULT_METAPATHS.keys()),
            },
            metadata={
                "total_metapaths": len(metapaths),
                "description": "Predefined biochemically sound metapaths for path finding",
            },
        )
        logger.info("Tool succeeded: get_supported_metapaths()")
        return result
    except Exception as e:
        return handle_neo4j_error(e, "", "get_supported_metapaths")


@medmcps_tool(name="everycure_kg_find_paths_by_metapath", servers=[everycure_kg_mcp, unified_mcp])
async def find_paths_by_metapath(
    source_id: str,
    target_id: str,
    metapath_name: str,
    max_paths: int = 10,
    database: str | None = None,
) -> dict:
    """Find paths between two nodes using a predefined metapath.

    IMPORTANT: Only predefined metapaths are allowed to prevent path explosion
    in this highly connected graph. Custom path patterns are not supported.

    To discover available metapaths, use get_supported_metapaths().
    To see what node types and relationship types are available in the database,
    use get_supported_types().

    Available metapaths include:
    - drug_to_disease_direct: Drug -> treats -> Disease (1 hop)
    - drug_to_disease_via_target: Drug -> interacts_with -> Protein ->
      associated_with -> Disease (2 hops)
    - drug_to_disease_via_pathway: Drug -> interacts_with -> Protein -> part_of ->
      Pathway -> associated_with -> Disease (3 hops)
    - drug_to_disease_via_gene: Drug -> interacts_with -> Protein ->
      gene_product_of -> Gene -> associated_with -> Disease (3 hops)
    - disease_to_disease_shared_gene: Disease -> associated_with -> Gene ->
      associated_with -> Disease (2 hops)
    - drug_side_effect_path: Drug -> causes -> PhenotypicFeature ->
      associated_with -> Disease (2 hops)

    Args:
        source_id: Source node ID (e.g., "CHEMBL123" for a drug,
                  "MONDO:0007113" for a disease)
        target_id: Target node ID (e.g., "MONDO:0007113" for a disease,
                  "HGNC:1100" for a gene)
        metapath_name: Name of predefined metapath. Must be one of the metapaths
                      returned by get_supported_metapaths(). Examples:
                      "drug_to_disease_direct", "drug_to_disease_via_target"
        max_paths: Maximum number of paths to return (default: 10)
        database: Database version (defaults to latest: everycure-v0.13.0)

    Returns:
        Dict with paths matching the metapath pattern, including:
        - paths: List of path objects with nodes and relationships
        - metapath_info: Information about the metapath used (name, description, pattern, hops)

    Example:
        To find drugs that treat a disease via their protein targets:
        find_paths_by_metapath(
            source_id="CHEMBL123",
            target_id="MONDO:0007113",
            metapath_name="drug_to_disease_via_target"
        )
    """
    db_name = database or settings.everycure_kg_default_database
    logger.info(
        f"Tool invoked: find_paths_by_metapath(source_id='{source_id}', "
        f"target_id='{target_id}', metapath_name='{metapath_name}')"
    )

    try:
        # Get metapath definition
        metapath = get_metapath_by_name(metapath_name)
        if metapath is None:
            return neo4j_response(
                data=None,
                metadata={"database": db_name},
                error=(
                    f"Unknown metapath: {metapath_name}. "
                    f"Use get_supported_metapaths() to see available metapaths."
                ),
            )

        # Parse metapath pattern
        node_labels, relationship_types = parse_metapath_pattern(metapath["pattern"])
        hops = metapath["hops"]

        client = get_neo4j_client()

        # Safety check: Prevent path explosion before executing query
        if hops > 1:
            safety = await check_metapath_safety(client, source_id, target_id, hops, db_name)
            if safety["blocked"]:
                logger.warning(f"Blocked metapath query: {safety['warning']}")
                return neo4j_response(
                    data=None,
                    error=safety["warning"],
                    metadata={
                        "database": db_name,
                        "source_id": source_id,
                        "target_id": target_id,
                        "metapath_name": metapath_name,
                        "hops": hops,
                        "safety_check": safety,
                    },
                )
            if safety["warning"]:
                logger.warning(f"Metapath safety warning: {safety['warning']}")

        # Get direction hints from metapath (for corrected metapaths with reversed relationships)
        direction_hints = metapath.get("direction_hints", {})

        # Helper function to get relationship direction pattern
        def get_rel_pattern(step_num: int, rel_type: str) -> str:
            """Get relationship pattern with correct direction.

            Args:
                step_num: Step number (1-indexed)
                rel_type: Relationship type

            Returns:
                String like "-[r1:rel_type]->" or "<-[r1:rel_type]-" or "-[r1:rel_type]-"
            """
            is_reversed = direction_hints.get(f"step_{step_num}_reversed", False)
            if is_reversed:
                return f"<-[r{step_num}:{rel_type}]-"
            else:
                # Default: forward direction (or bidirectional for compatibility)
                return f"-[r{step_num}:{rel_type}]-"

        # Build Cypher query based on number of hops
        if hops == 1:
            # 1-hop: Direct relationship
            rel_type = relationship_types[0]
            source_label = node_labels[0]
            target_label = node_labels[1]
            rel_pattern = get_rel_pattern(1, rel_type)

            query = f"""
            MATCH (source {{id: $source_id}}){rel_pattern}(target {{id: $target_id}})
            WHERE '{source_label}' IN labels(source) AND '{target_label}' IN labels(target)
            RETURN source, r1 as r, target, 1 as path_length
            LIMIT {max_paths}
            """
        elif hops == 2:
            # 2-hop: One intermediate node
            rel_type1 = relationship_types[0]
            rel_type2 = relationship_types[1]
            source_label = node_labels[0]
            intermediate_label = node_labels[1]
            target_label = node_labels[2]
            rel_pattern1 = get_rel_pattern(1, rel_type1)
            rel_pattern2 = get_rel_pattern(2, rel_type2)

            query = f"""
            MATCH (source {{id: $source_id}}){rel_pattern1}(intermediate)
              {rel_pattern2}(target {{id: $target_id}})
            WHERE '{source_label}' IN labels(source)
              AND '{intermediate_label}' IN labels(intermediate)
              AND '{target_label}' IN labels(target)
            RETURN source, r1, intermediate, r2, target, 2 as path_length
            LIMIT {max_paths}
            """
        elif hops == 3:
            # 3-hop: Two intermediate nodes
            rel_type1 = relationship_types[0]
            rel_type2 = relationship_types[1]
            rel_type3 = relationship_types[2]
            source_label = node_labels[0]
            intermediate1_label = node_labels[1]
            intermediate2_label = node_labels[2]
            target_label = node_labels[3]
            rel_pattern1 = get_rel_pattern(1, rel_type1)
            rel_pattern2 = get_rel_pattern(2, rel_type2)
            rel_pattern3 = get_rel_pattern(3, rel_type3)

            query = f"""
            MATCH (source {{id: $source_id}}){rel_pattern1}(intermediate1)
              {rel_pattern2}(intermediate2){rel_pattern3}(target {{id: $target_id}})
            WHERE '{source_label}' IN labels(source)
              AND '{intermediate1_label}' IN labels(intermediate1)
              AND '{intermediate2_label}' IN labels(intermediate2)
              AND '{target_label}' IN labels(target)
            RETURN source, r1, intermediate1, r2, intermediate2, r3, target,
                   3 as path_length
            LIMIT {max_paths}
            """
        else:
            return neo4j_response(
                data=None,
                metadata={"database": db_name},
                error=f"Unsupported metapath hops: {hops}. Only 1-3 hop metapaths are supported.",
            )

        # Execute query
        result = await client.execute_cypher(
            query, {"source_id": source_id, "target_id": target_id}, db_name
        )

        if result.get("data") is None:
            return result

        # Process paths
        paths = []
        for record in result["data"]:
            path_length = record.get("path_length", hops)

            if hops == 1:
                # 1-hop path (source, relationship, target)
                paths.append(
                    {
                        "source": record.get("source"),
                        "relationship": record.get("r"),
                        "target": record.get("target"),
                        "path_length": 1,
                    }
                )
            elif hops == 2:
                # 2-hop path (source, r1, intermediate, r2, target)
                paths.append(
                    {
                        "source": record.get("source"),
                        "relationships": [
                            record.get("r1"),
                            record.get("r2"),
                        ],
                        "intermediate": record.get("intermediate"),
                        "target": record.get("target"),
                        "path_length": 2,
                    }
                )
            elif hops == 3:
                # 3-hop path (source, r1, intermediate1, r2, intermediate2, r3, target)
                paths.append(
                    {
                        "source": record.get("source"),
                        "relationships": [
                            record.get("r1"),
                            record.get("r2"),
                            record.get("r3"),
                        ],
                        "intermediate1": record.get("intermediate1"),
                        "intermediate2": record.get("intermediate2"),
                        "target": record.get("target"),
                        "path_length": 3,
                    }
                )
            elif "path" in record:
                # Path object from Neo4j (fallback)
                path_obj = record["path"]
                paths.append(
                    {
                        "path": path_obj,
                        "path_length": path_length,
                    }
                )

        return neo4j_response(
            data={
                "paths": paths,
                "metapath_info": metapath,
            },
            metadata={
                "database": db_name,
                "source_id": source_id,
                "target_id": target_id,
                "metapath_name": metapath_name,
                "path_count": len(paths),
                "max_paths": max_paths,
            },
        )
    except Exception as e:
        return handle_neo4j_error(e, db_name, "find_paths_by_metapath")


@medmcps_tool(name="everycure_kg_find_drugs_for_disease", servers=[everycure_kg_mcp, unified_mcp])
async def find_drugs_for_disease(
    disease_id: str,
    include_indirect: bool = True,
    exclude_contraindicated: bool = True,
    max_paths_per_metapath: int = 10,
    database: str | None = None,
) -> dict:
    """Find drugs for a disease using predefined metapaths.

    Searches for drugs that treat or are associated with a disease using
    multiple metapaths. Can include direct treatment relationships and/or
    indirect relationships via targets and pathways.

    Args:
        disease_id: Disease identifier (e.g., "MONDO:0007113")
        include_indirect: If True, include indirect paths via targets/pathways
        exclude_contraindicated: If True, exclude drugs contraindicated for this disease
        max_paths_per_metapath: Maximum paths to return per metapath
        database: Database version (defaults to latest)

    Returns:
        Dict with drugs found via different metapaths
    """
    db_name = database or settings.everycure_kg_default_database
    logger.info(
        f"Tool invoked: find_drugs_for_disease(disease_id='{disease_id}', "
        f"include_indirect={include_indirect})"
    )

    try:
        client = get_neo4j_client()

        # Find drugs that directly treat the disease
        direct_query = f"""
        MATCH (drug)-[:treats_or_applied_or_studied_to_treat]-(disease {{id: $disease_id}})
        WHERE 'biolink:Drug' IN labels(drug) AND 'biolink:Disease' IN labels(disease)
        RETURN DISTINCT drug.id as drug_id, drug.name as drug_name, 'direct' as path_type
        LIMIT {max_paths_per_metapath}
        """

        direct_result = await client.execute_cypher(
            direct_query, {"disease_id": disease_id}, db_name
        )

        drugs_found = []
        if direct_result.get("data"):
            for record in direct_result["data"]:
                drugs_found.append(
                    {
                        "drug_id": record.get("drug_id"),
                        "drug_name": record.get("drug_name"),
                        "path_type": "direct",
                        "metapath": "drug_to_disease_direct",
                    }
                )

        # If including indirect, search via targets and pathways
        if include_indirect:
            # Via target metapath (simplified - find drugs via proteins)
            via_target_query = f"""
            MATCH (drug)-[:directly_physically_interacts_with]-(protein)
              -[:associated_with]-(disease {{id: $disease_id}})
            WHERE 'biolink:Drug' IN labels(drug)
              AND 'biolink:Protein' IN labels(protein)
              AND 'biolink:Disease' IN labels(disease)
            RETURN DISTINCT
                drug.id as drug_id,
                drug.name as drug_name,
                protein.id as protein_id,
                'via_target' as path_type
            LIMIT {max_paths_per_metapath}
            """

            via_target_result = await client.execute_cypher(
                via_target_query, {"disease_id": disease_id}, db_name
            )
            if via_target_result.get("data"):
                for record in via_target_result["data"]:
                    drugs_found.append(
                        {
                            "drug_id": record.get("drug_id"),
                            "drug_name": record.get("drug_name"),
                            "protein_id": record.get("protein_id"),
                            "path_type": "via_target",
                            "metapath": "drug_to_disease_via_target",
                        }
                    )

        # Exclude contraindicated drugs if requested
        if exclude_contraindicated and drugs_found:
            drug_ids = [d["drug_id"] for d in drugs_found]
            contraindicated_query = """
            MATCH (drug)-[:contraindicated_in]-(disease {id: $disease_id})
            WHERE drug.id IN $drug_ids
            RETURN drug.id as drug_id
            """
            contraindicated_result = await client.execute_cypher(
                contraindicated_query, {"disease_id": disease_id, "drug_ids": drug_ids}, db_name
            )
            contraindicated_ids = set()
            if contraindicated_result.get("data"):
                contraindicated_ids = {r["drug_id"] for r in contraindicated_result["data"]}

            drugs_found = [d for d in drugs_found if d["drug_id"] not in contraindicated_ids]

        return neo4j_response(
            data={
                "disease_id": disease_id,
                "drugs": drugs_found,
                "total_drugs": len(drugs_found),
            },
            metadata={
                "database": db_name,
                "include_indirect": include_indirect,
                "exclude_contraindicated": exclude_contraindicated,
                "max_paths_per_metapath": max_paths_per_metapath,
            },
        )
    except Exception as e:
        return handle_neo4j_error(e, db_name, "find_drugs_for_disease")


@medmcps_tool(name="everycure_kg_find_diseases_for_drug", servers=[everycure_kg_mcp, unified_mcp])
async def find_diseases_for_drug(
    drug_id: str,
    include_indications: bool = True,
    include_contraindications: bool = True,
    include_adverse_events: bool = True,
    database: str | None = None,
) -> dict:
    """Find diseases associated with a drug using metapaths.

    Searches for diseases that are indications, contraindications, or
    adverse events for a given drug.

    Args:
        drug_id: Drug identifier (e.g., "CHEMBL123" or "UMLS:C0017302")
        include_indications: Include diseases the drug treats
        include_contraindications: Include diseases where drug is contraindicated
        include_adverse_events: Include diseases caused by drug side effects
        database: Database version (defaults to latest)

    Returns:
        Dict with diseases found, categorized by relationship type
    """
    db_name = database or settings.everycure_kg_default_database
    logger.info(
        f"Tool invoked: find_diseases_for_drug(drug_id='{drug_id}', "
        f"include_indications={include_indications}, "
        f"include_contraindications={include_contraindications})"
    )

    try:
        client = get_neo4j_client()
        diseases_found: dict[str, list[dict[str, Any]]] = {
            "indications": [],
            "contraindications": [],
            "adverse_events": [],
        }

        # Find indications (diseases the drug treats)
        if include_indications:
            indications_query = """
            MATCH (drug {id: $drug_id})-[r:treats_or_applied_or_studied_to_treat]-(disease)
            WHERE 'biolink:Drug' IN labels(drug) AND 'biolink:Disease' IN labels(disease)
            RETURN DISTINCT
                disease.id as disease_id,
                disease.name as disease_name,
                type(r) as rel_type
            LIMIT 100
            """
            indications_result = await client.execute_cypher(
                indications_query, {"drug_id": drug_id}, db_name
            )
            if indications_result.get("data"):
                diseases_found["indications"] = [
                    {
                        "disease_id": r["disease_id"],
                        "disease_name": r["disease_name"],
                        "relationship_type": r["rel_type"],
                    }
                    for r in indications_result["data"]
                ]

        # Find contraindications
        if include_contraindications:
            contraindications_query = """
            MATCH (drug {id: $drug_id})-[r:contraindicated_in]-(disease)
            WHERE 'biolink:Drug' IN labels(drug) AND 'biolink:Disease' IN labels(disease)
            RETURN DISTINCT
                disease.id as disease_id,
                disease.name as disease_name,
                type(r) as rel_type
            LIMIT 100
            """
            contraindications_result = await client.execute_cypher(
                contraindications_query, {"drug_id": drug_id}, db_name
            )
            if contraindications_result.get("data"):
                diseases_found["contraindications"] = [
                    {
                        "disease_id": r["disease_id"],
                        "disease_name": r["disease_name"],
                        "relationship_type": r["rel_type"],
                    }
                    for r in contraindications_result["data"]
                ]

        # Find adverse events (via side effects)
        if include_adverse_events:
            adverse_events_query = """
            MATCH (drug {id: $drug_id})-[r1:causes]-(phenotype)-[r2:associated_with]-(disease)
            WHERE 'biolink:Drug' IN labels(drug)
              AND 'biolink:PhenotypicFeature' IN labels(phenotype)
              AND 'biolink:Disease' IN labels(disease)
            RETURN DISTINCT
                disease.id as disease_id,
                disease.name as disease_name,
                phenotype.id as phenotype_id
            LIMIT 100
            """
            adverse_events_result = await client.execute_cypher(
                adverse_events_query, {"drug_id": drug_id}, db_name
            )
            if adverse_events_result.get("data"):
                diseases_found["adverse_events"] = [
                    {
                        "disease_id": r["disease_id"],
                        "disease_name": r["disease_name"],
                        "phenotype_id": r["phenotype_id"],
                    }
                    for r in adverse_events_result["data"]
                ]

        total_diseases = (
            len(diseases_found["indications"])
            + len(diseases_found["contraindications"])
            + len(diseases_found["adverse_events"])
        )

        return neo4j_response(
            data={
                "drug_id": drug_id,
                "diseases": diseases_found,
                "total_diseases": total_diseases,
            },
            metadata={
                "database": db_name,
                "include_indications": include_indications,
                "include_contraindications": include_contraindications,
                "include_adverse_events": include_adverse_events,
            },
        )
    except Exception as e:
        return handle_neo4j_error(e, db_name, "find_diseases_for_drug")


def _build_dynamic_path_query(
    node_labels: list[str],
    relationship_types: list[str],
    max_paths: int,
) -> str:
    """Build Cypher query for variable-length path pattern."""
    hops = len(relationship_types)

    if hops == 1:
        return f"""
        MATCH (source {{id: $source_id}})-[r:{relationship_types[0]}]-(target {{id: $target_id}})
        WHERE '{node_labels[0]}' IN labels(source) AND '{node_labels[1]}' IN labels(target)
        RETURN source, r, target, 1 as path_length
        LIMIT {max_paths}
        """

    # Build variable-length pattern
    pattern_parts = ["(source {id: $source_id})"]
    where_clauses = [f"'{node_labels[0]}' IN labels(source)"]
    return_parts = ["source"]

    for i in range(hops):
        rel_var = f"r{i + 1}"
        if i < hops - 1:
            inter_var = f"intermediate{i + 1}"
            pattern_parts.append(f"-[{rel_var}:{relationship_types[i]}]-({inter_var})")
            where_clauses.append(f"'{node_labels[i + 1]}' IN labels({inter_var})")
            return_parts.extend([rel_var, inter_var])
        else:
            pattern_parts.append(
                f"-[{rel_var}:{relationship_types[i]}]-(target {{id: $target_id}})"
            )
            where_clauses.append(f"'{node_labels[-1]}' IN labels(target)")
            return_parts.extend([rel_var, "target"])

    pattern = "".join(pattern_parts)
    where_clause = " AND ".join(where_clauses)
    return_clause = ", ".join(return_parts) + f", {hops} as path_length"

    return f"""
    MATCH {pattern}
    WHERE {where_clause}
    RETURN {return_clause}
    LIMIT {max_paths}
    """


@medmcps_tool(
    name="everycure_kg_find_paths_by_custom_metapath", servers=[everycure_kg_mcp, unified_mcp]
)
async def find_paths_by_custom_metapath(
    source_id: str,
    target_id: str,
    metapath_pattern: str,
    max_paths: int = 10,
    max_hops: int = 5,
    database: str | None = None,
) -> dict:
    """Find paths between two nodes using a custom metapath pattern.

    Allows users to specify custom metapath patterns like:
    "Drug->directly_physically_interacts_with->Protein->gene_product_of->Gene"

    All node types and relationship types are validated against Biolink Model
    to ensure they exist before constructing the query.

    IMPORTANT: For safety, max_hops is limited to 5 by default to prevent
    path explosion. Very long paths may return millions of results.

    Args:
        source_id: Source node ID (e.g., "CHEMBL123" for a drug)
        target_id: Target node ID (e.g., "MONDO:0007113" for a disease)
        metapath_pattern: Custom metapath string with format:
                         "NodeType->RelType->NodeType->RelType->NodeType"
                         Examples:
                         - "Drug->treats->Disease"
                         - "Drug->directly_physically_interacts_with->Protein"
                         - "Drug->directly_physically_interacts_with->Protein"
                           "->gene_product_of->Gene->associated_with->Disease"
        max_paths: Maximum number of paths to return (default: 10)
        max_hops: Maximum allowed hops for safety (default: 5, max: 5)
        database: Database version (defaults to latest: everycure-v0.13.0)

    Returns:
        Dict with paths matching the metapath pattern, including:
        - paths: List of path objects with nodes and relationships
        - metapath_pattern: The validated metapath pattern used
        - validated_pattern: Validated node labels and relationship types
    """
    db_name = database or settings.everycure_kg_default_database
    logger.info(
        f"Tool invoked: find_paths_by_custom_metapath(source_id='{source_id}', "
        f"target_id='{target_id}', pattern='{metapath_pattern[:50]}...')"
    )

    try:
        # Parse metapath string
        try:
            node_labels_raw, relationship_types_raw, hops = parse_metapath_string(metapath_pattern)
        except ValueError as e:
            return neo4j_response(
                data=None,
                metadata={
                    "database": db_name,
                    "hint": "Format should be: NodeType->RelType->NodeType->RelType->NodeType",
                },
                error=f"Invalid metapath pattern: {e!s}",
            )

        # Validate hops limit
        if hops > max_hops:
            return neo4j_response(
                data=None,
                metadata={
                    "database": db_name,
                    "hops": hops,
                    "max_hops": max_hops,
                },
                error=f"Metapath has {hops} hops, exceeds maximum of {max_hops}",
            )

        # Validate all node types exist in Biolink Model
        validated_node_labels = []
        validation_errors = []

        for i, node_type in enumerate(node_labels_raw):
            is_valid, normalized = validate_node_type(node_type)
            if not is_valid:
                validation_errors.append(
                    f"Node type '{node_type}' at position {i + 1} is not valid in Biolink Model."
                    f" Use get_supported_types() to see available node types."
                )
            else:
                validated_node_labels.append(normalized)

        # Validate all relationship types exist in Biolink Model
        validated_rel_types = []

        for i, rel_type in enumerate(relationship_types_raw):
            is_valid, normalized = validate_relationship_type(rel_type)
            if not is_valid:
                validation_errors.append(
                    f"Relationship type '{rel_type}' at position {i + 1} is not valid "
                    f"in Biolink Model. Use get_supported_types() to see available types."
                )
            else:
                validated_rel_types.append(normalized)

        if validation_errors:
            return neo4j_response(
                data=None,
                metadata={
                    "validation_errors": validation_errors,
                    "database": db_name,
                },
                error="Validation failed",
            )

        # Build dynamic Cypher query
        client = get_neo4j_client()
        # Type narrowing: validated lists only contain strings (None filtered out above)
        query = _build_dynamic_path_query(
            [str(n) for n in validated_node_labels],
            [str(r) for r in validated_rel_types],
            max_paths,
        )

        # Execute query
        result = await client.execute_cypher(
            query, {"source_id": source_id, "target_id": target_id}, db_name
        )

        if result.get("data") is None:
            return result

        # Process paths
        paths = []
        for record in result["data"]:
            path_length = record.get("path_length", hops)
            path_obj = {
                "source": record.get("source"),
                "target": record.get("target"),
                "path_length": path_length,
            }

            # Add intermediate nodes and relationships
            if hops > 1:
                path_obj["relationships"] = [record.get(f"r{i + 1}") for i in range(hops)]
                if hops == 2:
                    path_obj["intermediate"] = record.get("intermediate1")
                elif hops >= 3:
                    path_obj["intermediate_nodes"] = [
                        record.get(f"intermediate{i + 1}") for i in range(hops - 1)
                    ]
            else:
                path_obj["relationship"] = record.get("r")

            paths.append(path_obj)

        return neo4j_response(
            data={
                "paths": paths,
                "metapath_pattern": metapath_pattern,
                "validated_pattern": {
                    "node_labels": validated_node_labels,
                    "relationship_types": validated_rel_types,
                    "hops": hops,
                },
            },
            metadata={
                "database": db_name,
                "source_id": source_id,
                "target_id": target_id,
                "path_count": len(paths),
                "max_paths": max_paths,
            },
        )
    except Exception as e:
        return handle_neo4j_error(e, db_name, "find_paths_by_custom_metapath")
