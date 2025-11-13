#!/usr/bin/env python3
"""
Main HTTP MCP Server
Mounts individual API servers at /tools/{api_name}/mcp
"""

import contextlib
import logging

from starlette.applications import Starlette
from starlette.routing import Mount

# IMPORTANT: Configure logging BEFORE initializing Sentry
# This ensures Sentry initialization messages are properly displayed
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)

# IMPORTANT: Initialize Sentry BEFORE importing server modules
# This ensures Sentry can properly instrument @mcp.tool decorators
from .sentry_config import init_sentry  # noqa: E402
from .settings import settings  # noqa: E402

# Initialize Sentry first - must happen before server imports
init_sentry()

log = logging.getLogger(__name__)

# Import server modules - their @medmcps_tool decorators automatically register tools with unified_mcp
# Note: Sentry must be initialized before server imports
from .servers import (  # noqa: E402
    biothings_server,
    chembl_server,
    ctg_server,
    gwas_server,
    kegg_server,
    myvariant_server,
    nci_server,
    nodenorm_server,  # noqa: F401 - imported for side effects (tool registration)
    omim_server,
    openfda_server,
    pathwaycommons_server,
    playbook_server,
    pubmed_server,
    reactome_server,
    uniprot_server,
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
    logger.info("  - Unified (all APIs): /tools/unified/mcp")
    logger.info("  - Reactome: /tools/reactome/mcp")
    logger.info("  - KEGG: /tools/kegg/mcp")
    logger.info("  - UniProt: /tools/uniprot/mcp")
    logger.info("  - OMIM: /tools/omim/mcp (requires API key)")
    logger.info("  - GWAS Catalog: /tools/gwas/mcp")
    logger.info("  - Pathway Commons: /tools/pathwaycommons/mcp")
    logger.info("  - ChEMBL: /tools/chembl/mcp")
    logger.info("  - ClinicalTrials.gov: /tools/ctg/mcp")
    logger.info("  - PubMed: /tools/pubmed/mcp")
    logger.info("  - OpenFDA: /tools/openfda/mcp")
    logger.info("  - MyVariant: /tools/myvariant/mcp")
    logger.info("  - BioThings: /tools/biothings/mcp")
    logger.info("  - NCI Clinical Trials: /tools/nci/mcp (requires API key)")
    logger.info("  - Drug Repurposing Playbooks: /tools/playbooks/mcp")

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
        await stack.enter_async_context(pubmed_server.pubmed_mcp.session_manager.run())
        await stack.enter_async_context(
            openfda_server.openfda_mcp.session_manager.run()
        )
        await stack.enter_async_context(
            myvariant_server.myvariant_mcp.session_manager.run()
        )
        await stack.enter_async_context(
            biothings_server.biothings_mcp.session_manager.run()
        )
        await stack.enter_async_context(nci_server.nci_mcp.session_manager.run())
        await stack.enter_async_context(
            playbook_server.playbook_mcp.session_manager.run()
        )
        yield

    logger.info("Shutting down Biological APIs MCP Server...")


from .med_mcp_server import unified_mcp  # noqa: E402

# Create Starlette app and mount all API servers

app = Starlette(
    routes=[
        Mount("/tools/unified", app=unified_mcp.streamable_http_app()),
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
        Mount("/tools/pubmed", app=pubmed_server.pubmed_mcp.streamable_http_app()),
        Mount("/tools/openfda", app=openfda_server.openfda_mcp.streamable_http_app()),
        Mount(
            "/tools/myvariant", app=myvariant_server.myvariant_mcp.streamable_http_app()
        ),
        Mount(
            "/tools/biothings", app=biothings_server.biothings_mcp.streamable_http_app()
        ),
        Mount("/tools/nci", app=nci_server.nci_mcp.streamable_http_app()),
        Mount(
            "/tools/playbooks", app=playbook_server.playbook_mcp.streamable_http_app()
        ),
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
    pubmed_server.pubmed_mcp.settings.host = host
    pubmed_server.pubmed_mcp.settings.port = port
    openfda_server.openfda_mcp.settings.host = host
    openfda_server.openfda_mcp.settings.port = port
    myvariant_server.myvariant_mcp.settings.host = host
    myvariant_server.myvariant_mcp.settings.port = port
    biothings_server.biothings_mcp.settings.host = host
    biothings_server.biothings_mcp.settings.port = port
    nci_server.nci_mcp.settings.host = host
    nci_server.nci_mcp.settings.port = port
    playbook_server.playbook_mcp.settings.host = host
    playbook_server.playbook_mcp.settings.port = port
    unified_mcp.settings.host = host
    unified_mcp.settings.port = port

    logger.info(f"Starting server on http://{host}:{port}")
    logger.info("MCP endpoints:")
    logger.info(f"  - Unified (all APIs): http://{host}:{port}/tools/unified/mcp")
    logger.info(f"  - Reactome: http://{host}:{port}/tools/reactome/mcp")
    logger.info(f"  - KEGG: http://{host}:{port}/tools/kegg/mcp")
    logger.info(f"  - UniProt: http://{host}:{port}/tools/uniprot/mcp")
    logger.info(f"  - OMIM: http://{host}:{port}/tools/omim/mcp")
    logger.info(f"  - GWAS Catalog: http://{host}:{port}/tools/gwas/mcp")
    logger.info(f"  - Pathway Commons: http://{host}:{port}/tools/pathwaycommons/mcp")
    logger.info(f"  - ChEMBL: http://{host}:{port}/tools/chembl/mcp")
    logger.info(f"  - ClinicalTrials.gov: http://{host}:{port}/tools/ctg/mcp")
    logger.info(f"  - PubMed: http://{host}:{port}/tools/pubmed/mcp")
    logger.info(f"  - OpenFDA: http://{host}:{port}/tools/openfda/mcp")
    logger.info(f"  - MyVariant: http://{host}:{port}/tools/myvariant/mcp")
    logger.info(f"  - BioThings: http://{host}:{port}/tools/biothings/mcp")
    logger.info(f"  - NCI Clinical Trials: http://{host}:{port}/tools/nci/mcp")

    # Run the Starlette app with uvicorn
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    entry_point()
