import os
from dataclasses import dataclass


def _get_env(name: str, default: str | None = None, required: bool = False) -> str:
    value = os.getenv(name, default)
    if required and not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value or ""


@dataclass
class Settings:
    openai_endpoint: str
    openai_key: str
    openai_deployment: str
    openai_embedding_deployment: str
    openai_api_version: str
    search_endpoint: str
    search_admin_key: str
    search_index: str
    top_k: int = 3
    max_history_turns: int = 6


def load_settings() -> Settings:
    return Settings(
        openai_endpoint=_get_env("AZURE_OPENAI_ENDPOINT", required=True),
        openai_key=_get_env("AZURE_OPENAI_KEY", required=True),
        openai_deployment=_get_env("AZURE_OPENAI_DEPLOYMENT", required=True),
        openai_embedding_deployment=_get_env("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", required=True),
        openai_api_version=_get_env("AZURE_OPENAI_API_VERSION", "2024-02-01"),
        search_endpoint=_get_env("AZURE_AI_SEARCH_ENDPOINT", required=True),
        search_admin_key=_get_env("AZURE_AI_SEARCH_ADMIN_KEY", required=True),
        search_index=_get_env("AZURE_AI_SEARCH_INDEX", "customer-support-index"),
    )
