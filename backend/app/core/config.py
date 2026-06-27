from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "AgentNexus"
    app_version: str = "0.1.0"
    debug: bool = False
    api_prefix: str = "/api/v1"

    # LLM providers (configure via environment)
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    google_api_key: str | None = None
    gemini_api_key: str | None = None
    xai_api_key: str | None = None
    ollama_enabled: bool = False
    ollama_base_url: str = "http://127.0.0.1:11434"
    default_model: str = "gemini-2.5-flash"
    supervisor_model: str | None = None

    database_url: str = (
        "postgresql+asyncpg://agentnexus:agentnexus@localhost:5432/agentnexus"
    )

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24

    def validate_secrets(self) -> None:
        import os
        if not self.debug and self.jwt_secret_key == "change-me-in-production":
            # Local dev convenience only
            if os.environ.get("ALLOW_INSECURE_DEV_JWT") != "1":
                raise RuntimeError(
                    "CRITICAL: jwt_secret_key must be set to a strong secret in production. "
                    "Set JWT_SECRET_KEY in .env (VPS) or environment. "
                    "For local dev only: ALLOW_INSECURE_DEV_JWT=1 or set a custom JWT_SECRET_KEY."
                )

    cors_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "https://agentnexus.mrgeo888.workers.dev,"
        "https://agentnexus.dev,https://www.agentnexus.dev,"
        "https://obolla.com,https://www.obolla.com"
    )

    google_oauth_client_id: str | None = None

    signup_credits_usd: float = 5.0
    platform_admin_emails: str = "mrgeo888@gmail.com,geowahaha@gmail.com"
    billing_topup_max_usd: float = 100.0
    platform_fee_percent: float = 20.0

    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None
    stripe_success_url: str = (
        "https://agentnexus.mrgeo888.workers.dev/billing?stripe=success"
    )
    stripe_cancel_url: str = (
        "https://agentnexus.mrgeo888.workers.dev/billing?stripe=cancel"
    )

    aibotauth_mcp_url: str = "https://aibotauth.com/api/mcp"
    aibotauth_base_url: str = "https://aibotauth.com"
    aibotauth_mcp_api_key: str | None = None

    notify_worker_url: str | None = "https://obolla.com"
    obolla_public_url: str = "https://obolla.com"
    internal_notify_secret: str | None = None

    smart_farm_mqtt_enabled: bool = True
    smart_farm_mqtt_host: str = "mqtt"
    smart_farm_mqtt_port: int = 1883
    smart_farm_mqtt_username: str | None = None
    smart_farm_mqtt_password: str | None = None
    smart_farm_mqtt_client_id: str = "obolla-smart-farm-ingest"
    smart_farm_mqtt_topic_wildcard: str = "obolla/farm/+/telemetry"
    smart_farm_mqtt_public_host: str = "43.128.75.149"
    smart_farm_mqtt_tls_port: int = 8883
    smart_farm_auto_export_enabled: bool = True
    smart_farm_auto_export_interval_seconds: int = 3600

    # Agent-Ready run archive (before[]/after[] per site in agent-ready-sites/)
    agent_ready_archive_root: str | None = None
    agent_ready_archive_git: bool = True
    agent_ready_archive_git_push: bool = False
    agent_ready_coach_model: str = "gemini-2.5-flash"
    agent_ready_rescan_email_enabled: bool = True

    resend_api_key: str | None = None
    obolla_from_email: str = "OBOLLA Agent-Ready <noreply@obolla.com>"


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    s.validate_secrets()
    return s


settings = get_settings()