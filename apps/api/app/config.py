"""Application configuration via pydantic-settings.

Settings are read from environment variables / `.env`. No secrets are ever
committed — see `.env.example` for the full list.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_ignore_empty=True)

    database_url: str = "postgresql+asyncpg://shramiksathi:shramiksathi@localhost:5432/shramiksathi"
    cors_origins: str = "http://localhost:3001"

    # §106-107: minimum wage is set by the Minimum Remuneration Fixation
    # Committee (updated every 2 years). This is the current floor in NPR/month
    # and must be bumped whenever a new fixation is published.
    minimum_monthly_wage: float = 19550.0

    # Gemini API key for the RAG "Analyse with AI" feature. When empty the
    # endpoint returns a graceful 503 and the app keeps working deterministically.
    gemini_api_key: str = ""

    # Server secret used to derive the AES-256-GCM key that encrypts users'
    # digital-signature private keys at rest (see crypto.py). MUST be set to a
    # long random value in production — the DB alone must never be enough to
    # forge a signature.
    signing_secret: str = "dev-signing-secret-change-me"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
