from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "development"
    PORT: int = 8000
    DATA_DIR: Path = Path("./data")
    STATIC_DIR: Path | None = Path("../frontend/dist")
    FRONTEND_ORIGIN: str = "http://localhost:5173"
    LOG_LEVEL: str = "INFO"

    MAX_UPLOAD_MB: int = 25
    MAX_ROWS: int = 250_000
    MAX_COLUMNS: int = 200
    SESSION_TTL_HOURS: int = 24
    MAX_SESSIONS_IN_MEMORY: int = 8
    RATE_LIMIT_PER_MIN: int = 120

    LLM_ENABLED: bool = True
    LLM_PROVIDER_ORDER: str = "groq,ollama"
    LLM_TIMEOUT_SECONDS: int = 12
    LLM_REDACT_PII: bool = True
    GROQ_API_KEY: str = ""
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    GROQ_MODEL: str = "openai/gpt-oss-20b"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024


settings = Settings()
