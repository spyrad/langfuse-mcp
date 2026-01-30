"""Configuration settings for Langfuse MCP Server."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Langfuse API Configuration
    langfuse_secret_key: str
    langfuse_public_key: str
    langfuse_host: str

    # Server Configuration
    mcp_server_port: int = 8010
    log_level: str = "INFO"

    # SSL Configuration
    langfuse_verify_ssl: bool = True

    @property
    def langfuse_base_url(self) -> str:
        """Return the base URL for Langfuse API."""
        return self.langfuse_host.rstrip("/")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
