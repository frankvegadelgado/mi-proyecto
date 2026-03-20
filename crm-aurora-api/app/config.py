from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    aurora_host: str = "localhost"
    aurora_port: int = 5432
    aurora_db: str = "odoo_crm"
    aurora_user: str = "crm_user"
    aurora_password: str = "password"

    @property
    def async_database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.aurora_user}:{self.aurora_password}"
            f"@{self.aurora_host}:{self.aurora_port}/{self.aurora_db}"
        )

    @property
    def sync_database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.aurora_user}:{self.aurora_password}"
            f"@{self.aurora_host}:{self.aurora_port}/{self.aurora_db}"
        )

    secret_key: str = "dev-secret"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    odoo_url: str = ""
    odoo_db: str = ""
    odoo_user: str = ""
    odoo_password: str = ""

    app_env: str = "development"
    log_level: str = "info"


@lru_cache
def get_settings() -> Settings:
    return Settings()
