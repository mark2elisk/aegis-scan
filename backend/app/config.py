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

    # Orígenes permitidos por CORS, separados por comas. En desarrollo apunta
    # al frontend local; en producción hay que ponerlo al dominio real.
    cors_origins: str = "http://localhost:3000"

    # Límite de peticiones a /scan por IP y por minuto.
    rate_limit_per_minute: int = 10

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def cors_origins_list(self) -> list[str]:
        return [origen.strip() for origen in self.cors_origins.split(",") if origen.strip()]


settings = Settings()
