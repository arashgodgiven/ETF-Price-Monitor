from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "ETF Price Monitor"
    app_version: str = "1.0.0"
    environment: str = "development"
    log_level: str = "INFO"

    # Database
    database_url: str = (
        "postgresql+asyncpg://etf_user:etf_password@localhost:5432/etf_monitor"
    )

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:80"

    # Upload constraints
    max_upload_size_bytes: int = 1_048_576  # 1 MB
    max_constituents: int = 500

    @property
    def allowed_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"
    

@lru_cache
def get_settings() -> Settings:
    return Settings()