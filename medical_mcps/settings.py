"""
Configuration settings for MCP server using pydantic-settings

Environment variables are automatically loaded and take precedence over defaults.
Field names are automatically converted to uppercase for env var lookup:
- sentry_dsn → SENTRY_DSN
- mcp_host → MCP_HOST
- mcp_port → MCP_PORT
etc.

Environment variables can be set:
1. Directly in the environment (highest priority)
2. In a .env file in the project root
3. As default values in the class (lowest priority)
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerSettings(BaseSettings):
    """
    Server configuration with environment variable support.

    All settings can be overridden via environment variables.
    Example: export SENTRY_DSN="your-dsn-here"
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # Config dict keys are case-insensitive
        extra="ignore",  # Ignore extra fields from env vars
        env_ignore_empty=True,  # Ignore empty string env vars
    )

    # Server configuration
    mcp_host: str = "0.0.0.0"
    # Railway provides PORT env var, fallback to MCP_PORT for local dev
    mcp_port: int = 8000

    # Sentry configuration (optional)
    sentry_dsn: str | None = None
    sentry_traces_sample_rate: float = 1.0  # Capture 100% of transactions for tracing
    sentry_send_default_pii: bool = True  # Set to True to include tool inputs/outputs
    sentry_enable_logs: bool = True  # Enable sending logs to Sentry
    sentry_profile_session_sample_rate: float = 1.0  # Profile 100% of profile sessions
    sentry_profile_lifecycle: str = (
        "trace"  # Automatically run profiler when there's an active transaction
    )

    def get_port(self) -> int:
        """Get port from PORT env var (Railway) or mcp_port setting"""
        import os

        return int(os.getenv("PORT", self.mcp_port))


# Global settings instance
settings = ServerSettings()
