from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de AegisScan, leída de variables de entorno (.env)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    clamd_host: str = "localhost"
    clamd_port: int = 3310
    clamd_timeout_seconds: int = 30

    max_upload_mb: int = 25

    ai_provider: str = "openai"  # "openai" | "none"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


settings = Settings()
