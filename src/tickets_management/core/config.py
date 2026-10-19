"""Application configuration loaded from environment variables."""

from enum import StrEnum
from functools import lru_cache

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    """Allowed runtime environments."""

    local = "local"
    staging = "staging"
    production = "production"


class Settings(BaseSettings):
    """Application settings sourced from environment variables and `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    environment: Environment = Environment.local

    # Required
    database_url: str
    redis_url: str

    # Optional for now
    telegram_bot_token: str | None = None
    jwt_secret: str | None = None

    # Defaults
    otp_ttl_seconds: int = 3000


def _format_config_error(exc: ValidationError) -> str:
    """Turn a Settings validation error into a readable, env-var-centric message."""
    missing: list[str] = []
    invalid: list[str] = []
    for error in exc.errors():
        env_var = str(error["loc"][0]).upper() if error["loc"] else "UNKNOWN"
        if error["type"] == "missing":
            missing.append(env_var)
        else:
            invalid.append(f"{env_var} ({error['msg']})")

    problems: list[str] = []
    if missing:
        problems.append("missing required variable(s): " + ", ".join(sorted(missing)))
    if invalid:
        problems.append("invalid value(s): " + ", ".join(invalid))

    return (
        "Invalid configuration: "
        + "; ".join(problems)
        + ". Set these in your .env file (see .env.example) "
        "or export them in the shell before starting the app."
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached (singleton) Settings instance."""
    try:
        # Required fields are populated from the environment.
        return Settings()  # pyright: ignore[reportCallIssue]
    except ValidationError as exc:
        raise RuntimeError(_format_config_error(exc)) from exc
