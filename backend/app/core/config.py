"""Application configuration via environment variables."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Career Intelligence Agent"
    app_version: str = "1.0.0"
    debug: bool = True

    # Database — defaults to SQLite for local MVP; set DATABASE_URL for Postgres/Supabase
    database_url: str = "sqlite:///./career_intelligence.db"

    # LLM
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    llm_temperature: float = 0.3
    demo_mode: bool = False  # force heuristic agents even if API key present

    # Storage
    upload_dir: Path = Path(__file__).resolve().parent.parent / "uploads"
    max_upload_mb: int = 10

    # Vector store
    chroma_persist_dir: Path = Path(__file__).resolve().parent.parent / "data" / "chroma"
    rag_collection_name: str = "career_knowledge"

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def llm_enabled(self) -> bool:
        return bool(self.openai_api_key) and not self.demo_mode


@lru_cache
def get_settings() -> Settings:
    return Settings()
