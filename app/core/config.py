from typing import Literal, Self

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./tickets.db"

    jwt_secret_key: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    bcrypt_rounds: int = 12

    triage_provider: Literal["keywords", "anthropic"] = "keywords"
    anthropic_api_key: SecretStr | None = None
    anthropic_model: str = "claude-opus-5-5"
    triage_timeout_seconds: float = 20.0

    @model_validator(mode="after")
    def check_triage_settings(self) -> Self:
        if self.triage_provider == "anthropic" and not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY é obrigatória quando TRIAGE_PROVIDER=anthropic")
        return self


settings = Settings()
