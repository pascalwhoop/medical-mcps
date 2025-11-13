"""
Central MCP server hub.

Contains the unified FastMCP instance and the tool decorator that allows
registering tools with multiple FastMCP servers simultaneously.
"""

from typing import Callable
from mcp.server.fastmcp import FastMCP

# Create unified FastMCP server
unified_mcp = FastMCP(
    "biological-apis-unified",
    stateless_http=True,
    json_response=True,
)


def tool(name: str, servers: list[FastMCP], **kwargs):
    """
    Decorator that registers a tool with multiple FastMCP servers.
    
    Args:
        name: Tool name
        servers: List of FastMCP instances to register with
        **kwargs: Additional arguments passed to FastMCP.tool()
    
    Usage:
        from medical_mcps.med_mcp_server import unified_mcp, tool as medmcps_tool
        
        @medmcps_tool(name="mygene_get_gene", servers=[biothings_mcp, unified_mcp])
        async def mygene_get_gene(...):
            ...
    """
    def decorator(func: Callable):
        # Register with each server
        for server in servers:
            server.tool(name=name, **kwargs)(func)
        return func
    return decorator

