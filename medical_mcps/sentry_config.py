#!/usr/bin/env python3
"""
Sentry configuration and initialization
Must be imported and initialized BEFORE any @mcp.tool decorators are registered
"""

import logging
import os

import sentry_sdk
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration
from sentry_sdk.integrations.mcp import MCPIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from .settings import settings

log = logging.getLogger(__name__)


def init_sentry() -> None:
    """
    Initialize Sentry if DSN is provided.

    This must be called BEFORE any @mcp.tool decorators are registered
    to ensure proper instrumentation of MCP tools.
    """
    if not settings.sentry_dsn:
        log.debug("Sentry DSN not provided, skipping Sentry initialization")
        return

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        # Add data like request headers and IP for users
        # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
        send_default_pii=settings.sentry_send_default_pii,
        # Enable sending logs to Sentry
        enable_logs=settings.sentry_enable_logs,
        # Set traces_sample_rate to 1.0 to capture 100% of transactions for tracing
        traces_sample_rate=settings.sentry_traces_sample_rate,
        # Set profile_session_sample_rate to 1.0 to profile 100% of profile sessions
        profile_session_sample_rate=settings.sentry_profile_session_sample_rate,
        # Set profile_lifecycle to "trace" to automatically run the profiler
        # when there is an active transaction
        profile_lifecycle=settings.sentry_profile_lifecycle,
        integrations=[
            # MCP integration - tracks tool executions, prompts, resources
            # IMPORTANT: This must be initialized before @mcp.tool decorators
            MCPIntegration(
                include_prompts=settings.sentry_send_default_pii,
            ),
            # Starlette integration - tracks HTTP requests, errors, performance
            StarletteIntegration(
                transaction_style="url",  # Use URL path as transaction name
                failed_request_status_codes={*range(500, 600)},  # Report 5xx errors
            ),
            # HTTPX integration - tracks outgoing HTTP requests from API clients
            HttpxIntegration(),
            # Asyncio integration - tracks async operations and context
            AsyncioIntegration(),
        ],
        # Set environment based on common env vars
        environment=os.getenv("ENVIRONMENT", "local"),
    )
    log.info(
        "Sentry initialized with MCP, Starlette, HTTPX, and asyncio integrations. "
        f"Tracing: {settings.sentry_traces_sample_rate * 100}%, "
        f"Profiling: {settings.sentry_profile_session_sample_rate * 100}%, "
        f"Logs: {'enabled' if settings.sentry_enable_logs else 'disabled'}"
    )
