#!/usr/bin/env python3
"""
Main HTTP MCP Server
Mounts individual API servers at /tools/{api_name}/mcp
"""

import contextlib
import logging
import os

import sentry_sdk
from sentry_sdk.integrations.mcp import MCPIntegration
from starlette.applications import Starlette
from starlette.routing import Mount

from .servers import (
    chembl_server,
    ctg_server,
    gwas_server,
    kegg_server,
    omim_server,
    pathwaycommons_server,
    reactome_server,
    uniprot_server,
)
from .settings import settings

# Initialize Sentry if DSN is provided
# The MCP integration is automatically enabled when mcp package is in dependencies
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        send_default_pii=settings.sentry_send_default_pii,
        integrations=[
            MCPIntegration(
                include_prompts=settings.sentry_send_default_pii,
            ),
        ],
        # Set environment based on common env vars
        environment=os.getenv("ENVIRONMENT", "production"),
    )

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)


# Suppress anyio.ClosedResourceError from FastMCP streamable HTTP transport
# This is expected behavior when streams close after responses are sent
class SuppressClosedResourceErrorFilter(logging.Filter):
    def filter(self, record):
        # Suppress ClosedResourceError messages from MCP streamable HTTP
        if "ClosedResourceError" in str(record.getMessage()):
            return False
        if "Error in message router" in str(record.getMessage()):
            return False
        return True


# Apply filter to MCP server loggers
mcp_logger = logging.getLogger("mcp.server.streamable_http")
mcp_logger.addFilter(SuppressClosedResourceErrorFilter())

logger = logging.getLogger(__name__)


@contextlib.asynccontextmanager
async def lifespan(app: Starlette):
    """Manage application lifespan - initialize all MCP server session managers"""
    logger.info("Starting Biological APIs MCP Server...")
    logger.info("Available API servers:")
    logger.info("  - Reactome: /tools/reactome/mcp")
    logger.info("  - KEGG: /tools/kegg/mcp")
    logger.info("  - UniProt: /tools/uniprot/mcp")
    logger.info("  - OMIM: /tools/omim/mcp (requires API key)")
    logger.info("  - GWAS Catalog: /tools/gwas/mcp")
    logger.info("  - Pathway Commons: /tools/pathwaycommons/mcp")
    logger.info("  - ChEMBL: /tools/chembl/mcp")
    logger.info("  - ClinicalTrials.gov: /tools/ctg/mcp")

    # Initialize all session managers using AsyncExitStack
    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(
            reactome_server.reactome_mcp.session_manager.run()
        )
        await stack.enter_async_context(kegg_server.kegg_mcp.session_manager.run())
        await stack.enter_async_context(
            uniprot_server.uniprot_mcp.session_manager.run()
        )
        await stack.enter_async_context(omim_server.omim_mcp.session_manager.run())
        await stack.enter_async_context(gwas_server.gwas_mcp.session_manager.run())
        await stack.enter_async_context(
            pathwaycommons_server.pathwaycommons_mcp.session_manager.run()
        )
        await stack.enter_async_context(chembl_server.chembl_mcp.session_manager.run())
        await stack.enter_async_context(ctg_server.ctg_mcp.session_manager.run())
        yield

    logger.info("Shutting down Biological APIs MCP Server...")


# Create Starlette app and mount all API servers
# Use streamable_http_app() method - it returns a Starlette app ready to mount
# This is the correct way per FastMCP documentation

app = Starlette(
    routes=[
        Mount(
            "/tools/reactome", app=reactome_server.reactome_mcp.streamable_http_app()
        ),
        Mount("/tools/kegg", app=kegg_server.kegg_mcp.streamable_http_app()),
        Mount("/tools/uniprot", app=uniprot_server.uniprot_mcp.streamable_http_app()),
        Mount("/tools/omim", app=omim_server.omim_mcp.streamable_http_app()),
        Mount("/tools/gwas", app=gwas_server.gwas_mcp.streamable_http_app()),
        Mount(
            "/tools/pathwaycommons",
            app=pathwaycommons_server.pathwaycommons_mcp.streamable_http_app(),
        ),
        Mount("/tools/chembl", app=chembl_server.chembl_mcp.streamable_http_app()),
        Mount("/tools/ctg", app=ctg_server.ctg_mcp.streamable_http_app()),
    ],
    lifespan=lifespan,
)


def entry_point():
    """Entry point for the script command"""
    import uvicorn

    host = settings.mcp_host
    port = settings.mcp_port

    # Configure all servers' host/port settings
    reactome_server.reactome_mcp.settings.host = host
    reactome_server.reactome_mcp.settings.port = port
    kegg_server.kegg_mcp.settings.host = host
    kegg_server.kegg_mcp.settings.port = port
    uniprot_server.uniprot_mcp.settings.host = host
    uniprot_server.uniprot_mcp.settings.port = port
    omim_server.omim_mcp.settings.host = host
    omim_server.omim_mcp.settings.port = port
    gwas_server.gwas_mcp.settings.host = host
    gwas_server.gwas_mcp.settings.port = port
    pathwaycommons_server.pathwaycommons_mcp.settings.host = host
    pathwaycommons_server.pathwaycommons_mcp.settings.port = port
    chembl_server.chembl_mcp.settings.host = host
    chembl_server.chembl_mcp.settings.port = port
    ctg_server.ctg_mcp.settings.host = host
    ctg_server.ctg_mcp.settings.port = port

    logger.info(f"Starting server on http://{host}:{port}")
    logger.info("MCP endpoints:")
    logger.info(f"  - Reactome: http://{host}:{port}/tools/reactome/mcp")
    logger.info(f"  - KEGG: http://{host}:{port}/tools/kegg/mcp")
    logger.info(f"  - UniProt: http://{host}:{port}/tools/uniprot/mcp")
    logger.info(f"  - OMIM: http://{host}:{port}/tools/omim/mcp")
    logger.info(f"  - GWAS Catalog: http://{host}:{port}/tools/gwas/mcp")
    logger.info(f"  - Pathway Commons: http://{host}:{port}/tools/pathwaycommons/mcp")
    logger.info(f"  - ChEMBL: http://{host}:{port}/tools/chembl/mcp")
    logger.info(f"  - ClinicalTrials.gov: http://{host}:{port}/tools/ctg/mcp")

    # Run the Starlette app with uvicorn
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    entry_point()
