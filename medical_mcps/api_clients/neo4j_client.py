"""
Every Cure Matrix Knowledge Graph Client
Connects to Neo4j database using the official Neo4j Python driver.
Documentation: https://neo4j.com/docs/python-manual/current/
"""

import asyncio
import logging
from typing import Any

from neo4j import GraphDatabase

from ..errors import is_transient_neo4j_error
from ..settings import settings

logger = logging.getLogger(__name__)


class Neo4jClient:
    """
    Client for interacting with Every Cure Matrix Knowledge Graph (Neo4j database)

    Note: Neo4j Python driver is synchronous, so we wrap all calls
    in asyncio.to_thread() to make them async-compatible.
    """

    def __init__(
        self,
        uri: str | None = None,
        username: str | None = None,
        password: str | None = None,
        database: str | None = None,
    ):
        """
        Initialize Neo4j client

        Args:
            uri: Neo4j database URI (defaults to EVERYCURE_KG_URI env var or settings)
            username: Database username (defaults to EVERYCURE_KG_USERNAME env var or settings)
            password: Database password (defaults to EVERYCURE_KG_PASSWORD env var or settings)
            database: Database name (defaults to EVERYCURE_KG_DEFAULT_DATABASE env var or settings)
        """
        self.uri = uri or settings.everycure_kg_uri
        self.username = username or settings.everycure_kg_username
        self.password = password or settings.everycure_kg_password
        self.database = database or settings.everycure_kg_default_database
        self._driver: Any | None = None

    def _reset_driver(self) -> None:
        if self._driver is not None:
            try:
                self._driver.close()
            except Exception:
                pass
        self._driver = None

    def _run_with_reconnect(self, func):
        try:
            return func()
        except Exception as exc:
            if is_transient_neo4j_error(exc):
                logger.warning("Neo4j connection error, retrying once: %s", exc)
                self._reset_driver()
                return func()
            raise

    def _get_driver(self):
        """Get or create Neo4j driver instance"""
        if self._driver is None:
            if not self.password:
                raise ValueError(
                    "EVERYCURE_KG_PASSWORD environment variable must be set. "
                    "Never commit passwords to code!"
                )
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
            )
        return self._driver

    async def _run_sync(self, func, *args, **kwargs):
        """Run synchronous function in thread pool"""
        return await asyncio.to_thread(func, *args, **kwargs)

    def _execute_query_sync(
        self, query: str, parameters: dict[str, Any] | None = None, database: str | None = None
    ) -> list[dict]:
        """
        Execute Cypher query synchronously

        Args:
            query: Cypher query string
            parameters: Query parameters (optional)
            database: Database name (overrides instance default)

        Returns:
            List of records as dictionaries
        """

        def run() -> list[dict]:
            driver = self._get_driver()
            db_name = database or self.database
            with driver.session(database=db_name) as session:
                result = session.run(query, parameters or {})
                records = []
                for record in result:
                    # Convert Neo4j Record to dict
                    record_dict = {}
                    for key in record.keys():
                        value = record[key]
                        # Convert Neo4j types to Python native types
                        if hasattr(value, "__class__"):
                            # Handle Neo4j Node, Relationship, Path objects
                            if value.__class__.__name__ == "Node":
                                record_dict[key] = {
                                    "id": value.id,
                                    "labels": list(value.labels),
                                    "properties": dict(value.items()),
                                }
                            elif value.__class__.__name__ == "Relationship":
                                record_dict[key] = {
                                    "id": value.id,
                                    "type": value.type,
                                    "start_node": value.start_node.id,
                                    "end_node": value.end_node.id,
                                    "properties": dict(value.items()),
                                }
                            elif value.__class__.__name__ == "Path":
                                record_dict[key] = {
                                    "nodes": [n.id for n in value.nodes],
                                    "relationships": [r.id for r in value.relationships],
                                }
                            else:
                                record_dict[key] = value
                        else:
                            record_dict[key] = value
                    records.append(record_dict)
                return records

        return self._run_with_reconnect(run)

    async def execute_cypher(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
        database: str | None = None,
    ) -> dict[str, Any]:
        """
        Execute Cypher query asynchronously

        Args:
            query: Cypher query string
            parameters: Query parameters (optional)
            database: Database name (overrides instance default)

        Returns:
            Dict with query results and metadata
        """
        db_name = database or self.database
        logger.info(f"Executing Cypher query on database '{db_name}': {query[:100]}...")
        try:
            records = await self._run_sync(self._execute_query_sync, query, parameters, db_name)
            return {
                "api_source": "Every Cure Matrix Knowledge Graph",
                "data": records,
                "metadata": {
                    "database": db_name,
                    "query": query,
                    "record_count": len(records),
                },
            }
        except Exception as e:
            logger.error(f"Error executing Cypher query: {e}", exc_info=True)
            return {
                "api_source": "Every Cure Matrix Knowledge Graph",
                "data": None,
                "metadata": {"error": f"Query error: {e!s}", "database": db_name},
            }

    def _get_schema_sync(self, database: str | None = None) -> dict[str, Any]:
        """Get database schema synchronously"""

        def run() -> dict[str, Any]:
            driver = self._get_driver()
            db_name = database or self.database
            with driver.session(database=db_name) as session:
                labels_result = session.run("CALL db.labels()")
                labels = [record["label"] for record in labels_result]
                rel_types_result = session.run("CALL db.relationshipTypes()")
                rel_types = [record["relationshipType"] for record in rel_types_result]
                prop_keys_result = session.run("CALL db.propertyKeys()")
                prop_keys = [record["propertyKey"] for record in prop_keys_result]
                return {
                    "labels": labels,
                    "relationship_types": rel_types,
                    "property_keys": prop_keys,
                }

        return self._run_with_reconnect(run)

    async def get_schema(self, database: str | None = None) -> dict[str, Any]:
        """
        Get database schema (labels, relationship types, property keys)

        Args:
            database: Database name (overrides instance default)

        Returns:
            Dict with schema information
        """
        db_name = database or self.database
        logger.info(f"Getting database schema for '{db_name}'")
        try:
            schema = await self._run_sync(self._get_schema_sync, db_name)
            return {
                "api_source": "Every Cure Matrix Knowledge Graph",
                "data": schema,
                "metadata": {
                    "database": db_name,
                    "label_count": len(schema["labels"]),
                    "relationship_type_count": len(schema["relationship_types"]),
                    "property_key_count": len(schema["property_keys"]),
                },
            }
        except Exception as e:
            logger.error(f"Error getting schema: {e}", exc_info=True)
            return {
                "api_source": "Every Cure Matrix Knowledge Graph",
                "data": None,
                "metadata": {"error": f"Schema error: {e!s}", "database": db_name},
            }

    def _get_stats_sync(self, database: str | None = None) -> dict[str, Any]:
        """Get database statistics synchronously"""

        def run() -> dict[str, Any]:
            driver = self._get_driver()
            db_name = database or self.database
            with driver.session(database=db_name) as session:
                node_count_result = session.run("MATCH (n) RETURN count(n) as count")
                node_count = node_count_result.single()["count"]
                rel_count_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                rel_count = rel_count_result.single()["count"]
                return {
                    "node_count": node_count,
                    "relationship_count": rel_count,
                }

        return self._run_with_reconnect(run)

    async def get_stats(self, database: str | None = None) -> dict[str, Any]:
        """
        Get database statistics (node count, relationship count)

        Args:
            database: Database name (overrides instance default)

        Returns:
            Dict with statistics
        """
        db_name = database or self.database
        logger.info(f"Getting database statistics for '{db_name}'")
        try:
            stats = await self._run_sync(self._get_stats_sync, db_name)
            return {
                "api_source": "Every Cure Matrix Knowledge Graph",
                "data": stats,
                "metadata": {"database": db_name},
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}", exc_info=True)
            return {
                "api_source": "Every Cure Matrix Knowledge Graph",
                "data": None,
                "metadata": {"error": f"Stats error: {e!s}", "database": db_name},
            }

    async def verify_connectivity(self) -> bool:
        """
        Verify connection to database

        Returns:
            True if connection successful
        """
        logger.info("Verifying database connectivity")
        try:
            driver = self._get_driver()
            await self._run_sync(driver.verify_connectivity)
            logger.info("Database connectivity verified")
            return True
        except Exception as e:
            logger.error(f"Database connectivity check failed: {e}", exc_info=True)
            return False

    async def close(self):
        """Close the database driver connection"""
        if self._driver:
            await self._run_sync(self._driver.close)
            self._driver = None
            logger.info("Database driver closed")
