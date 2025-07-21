from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import ConfigDict


class Settings(BaseSettings):
    # Database
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_HOST: str = "db"
    DB_PORT: str = "5432"
    DB_NAME: str = "res_match"

    # Security
    SECRET_KEY: str = "dev-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "ResMatch"

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["*"]

    # Optional: OpenAI API Key for future LLM features
    OPENAI_API_KEY: Optional[str] = None

    # Job Scraper Settings
    JOB_SCRAPER_TIMEOUT: int = 30
    JOB_SCRAPER_RETRIES: int = 3
    JOB_SCRAPER_DELAY: float = 1.0  # Delay between requests (seconds)
    JOB_SCRAPER_USER_AGENT: str = "res-match-api/1.0 (https://res-match.com/bot)"
    JOB_SCRAPER_MAX_RESULTS: int = 100  # Maximum results per search

    model_config = ConfigDict(
        env_file=".env", extra="ignore"  # Ignore extra environment variables
    )


settings = Settings()
