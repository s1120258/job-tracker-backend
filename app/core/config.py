from pydantic_settings import BaseSettings
from typing import Optional, Union
from pydantic import ConfigDict, Field, field_validator
from .aws_params import get_parameter
import json


class Settings(BaseSettings):
    # Database individual settings
    DB_USER: str = "postgres"
    DB_HOST: str = "db"
    DB_PORT: str = "5432"
    DB_NAME: str = "res_match"

    # Secure parameters from AWS Parameter Store with fallbacks
    DB_PASSWORD: str = Field(
        default_factory=lambda: get_parameter("/resmatch/DB_PASSWORD", "DB_PASSWORD")
        or "postgres"
    )
    SECRET_KEY: str = Field(
        default_factory=lambda: get_parameter("/resmatch/SECRET_KEY", "SECRET_KEY")
        or "dev-secret-key"
    )
    OPENAI_API_KEY: Optional[str] = Field(
        default_factory=lambda: get_parameter(
            "/resmatch/OPENAI_API_KEY", "OPENAI_API_KEY"
        )
    )
    SUPABASE_ANON_KEY: Optional[str] = Field(
        default_factory=lambda: get_parameter(
            "/resmatch/SUPABASE_KEY", "SUPABASE_ANON_KEY"
        )
    )

    # Other Supabase API settings
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None

    @property
    def DATABASE_URL(self) -> str:
        """Generate DATABASE_URL from individual DB settings"""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def SUPABASE_URL(self) -> str:
        """Generate SUPABASE_URL from DB_HOST (assuming Supabase pattern)"""
        if "supabase.co" in self.DB_HOST:
            # Extract project ID from db.{project_id}.supabase.co
            project_id = self.DB_HOST.replace("db.", "").replace(".supabase.co", "")
            return f"https://{project_id}.supabase.co"
        return f"https://{self.DB_HOST}"

    # Security
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "ResMatch"

    # CORS - Must be set via environment variable as JSON string
    # For development, defaults to localhost only for security
    BACKEND_CORS_ORIGINS: Union[str, list[str]] = [
        "http://localhost:3000",  # Local development
        "http://localhost:8000",  # Local development (alternative port)
        "https://resmatchai.com",  # Production frontend
        "https://res-match-ui.vercel.app",  # Vercel deployment
    ]

    # Job Scraper Settings
    JOB_SCRAPER_TIMEOUT: int = 30
    JOB_SCRAPER_RETRIES: int = 3
    JOB_SCRAPER_DELAY: float = 1.0  # Delay between requests (seconds)
    JOB_SCRAPER_USER_AGENT: str = "res-match-api/1.0 (https://res-match.com/bot)"
    JOB_SCRAPER_MAX_RESULTS: int = 100  # Maximum results per search

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from JSON string or return as-is if already a list"""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # If not valid JSON, treat as single origin
                return [v]
        return v

    model_config = ConfigDict(
        env_file=".env", extra="ignore"  # Ignore extra environment variables
    )


settings = Settings()
