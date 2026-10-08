from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "sqlite+aiosqlite:///./data/trustruntime.db"
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
