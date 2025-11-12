"""Pytest configuration and fixtures for MCP server tests"""

import logging
import os
import subprocess
import time
from typing import Generator

import pytest

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def server_url() -> str:
    """Get the server URL from environment or use default"""
    return os.getenv("MCP_SERVER_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def server_process(server_url: str) -> Generator[subprocess.Popen, None, None]:
    """
    Start the MCP server as a subprocess for the entire test session.
    The server will be available at the server_url.
    """
    # Extract host and port from URL
    if server_url.startswith("http://"):
        url_part = server_url[7:]
    elif server_url.startswith("https://"):
        url_part = server_url[8:]
    else:
        url_part = server_url

    if ":" in url_part:
        host, port = url_part.split(":", 1)
        port = int(port)
    else:
        host = "localhost"
        port = 8000

    # Set environment variables for the server
    env = os.environ.copy()
    env["MCP_HOST"] = host
    env["MCP_PORT"] = str(port)

    # Start the server process
    logger.info(f"Starting MCP server at {server_url}")
    process = subprocess.Popen(
        ["uv", "run", "mcp-server"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    # Wait for server to be ready
    # FastMCP doesn't have a /health endpoint, so we just wait for the process to start
    # and check if the port is accessible
    max_attempts = 60  # Increased to 60 attempts (30 seconds)
    for attempt in range(max_attempts):
        # Check if process has died
        if process.poll() is not None:
            stdout, _ = process.communicate(timeout=1)
            logger.error(f"Server process died. Output: {stdout}")
            raise RuntimeError(f"MCP server process terminated unexpectedly: {stdout}")

        try:
            # Try to connect to the MCP endpoint - it should return 405 for GET without proper headers
            # but at least it proves the server is running
            import socket

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                logger.info(f"MCP server is ready at {server_url}")
                # Give it a moment to fully initialize
                time.sleep(2)
                break
        except Exception:
            pass

        if attempt < max_attempts - 1:
            time.sleep(0.5)
        else:
            # Get error output if server failed to start
            try:
                stdout, _ = process.communicate(timeout=2)
                logger.error(f"Server failed to start. Output: {stdout}")
            except subprocess.TimeoutExpired:
                logger.error("Server process did not produce output")
            process.terminate()
            raise RuntimeError("MCP server failed to start within timeout period")
    else:
        process.terminate()
        raise RuntimeError("MCP server failed to start within timeout period")

    yield process

    # Cleanup: terminate the server
    logger.info("Stopping MCP server")
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


@pytest.fixture(scope="session")
def mcp_base_url(server_url: str) -> str:
    """Base URL for MCP endpoint"""
    return f"{server_url}/mcp"


@pytest.fixture(scope="session")
def omim_api_key() -> str:
    """Get OMIM API key from environment variable"""
    return os.getenv("OMIM_API_KEY", "")


def pytest_collection_modifyitems(config, items):
    """Skip OMIM tests if API key is not set"""
    omim_api_key = os.getenv("OMIM_API_KEY", "")
    if not omim_api_key:
        skip_omim = pytest.mark.skip(
            reason="OMIM_API_KEY environment variable not set"
        )
        for item in items:
            if "omim" in item.name.lower():
                item.add_marker(skip_omim)
