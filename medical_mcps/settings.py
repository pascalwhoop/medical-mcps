"""
Configuration settings for MCP server using pydantic-settings
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerSettings(BaseSettings):
    """Server configuration with environment variable support"""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Server configuration
    mcp_host: str = "0.0.0.0"
    # Railway provides PORT env var, fallback to MCP_PORT for local dev
    mcp_port: int = 8000

    # Sentry configuration (optional)
    sentry_dsn: str | None = None
    sentry_traces_sample_rate: float = 1.0
    sentry_send_default_pii: bool = False  # Set to True to include tool inputs/outputs

    def get_port(self) -> int:
        """Get port from PORT env var (Railway) or mcp_port setting"""
        import os

        return int(os.getenv("PORT", self.mcp_port))


# Global settings instance
settings = ServerSettings()
