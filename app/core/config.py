import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

def get_default_database_url() -> str:
    if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        return "sqlite+aiosqlite:////tmp/trustruntime.db"
    return "sqlite+aiosqlite:///./data/trustruntime.db"

class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = get_default_database_url()
    ollama_enabled: bool = False
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:0.6b"
    cloud_model_enabled: bool = False
    cloud_model_provider: str = "openai_compatible"
    cloud_model_base_url: str = ""
    cloud_model_api_key: str = ""
    cloud_model_name: str = ""
    neo4j_enabled: bool = False
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    embedding_model: str = ""
    max_compute_tokens: int = 12000
    max_attempts: int = 5
    sandbox_timeout_seconds: int = 5
    sandbox_memory_mb: int = 256
    log_level: str = "INFO"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

@lru_cache
def get_settings() -> Settings:
    return Settings()
