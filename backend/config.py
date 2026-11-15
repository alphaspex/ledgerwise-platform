# Inputs: process environment variables and optional backend/.env values parsed by Pydantic Settings.
# Outputs: Settings, get_settings(), and validated runtime configuration values.
# Explanation: Centralizes typed runtime configuration for D1, Meta Muse, JWT, Resend, Apollo, Cal.com, workers, and limits.
from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False)

    app_env: str = "development"
    cors_origins: List[str] = Field(default_factory=list)

    cloudflare_account_id: str = ""
    cloudflare_database_id: str = ""
    cloudflare_api_token: str = ""
    d1_api_base_url: str = "https://api.cloudflare.com/client/v4"

    api_token: str = ""
    muse_api_base_url: str = "https://api.meta.ai/v1"
    muse_model: str = "muse-ember-1.0"
    muse_reasoning_effort: str = "medium"
    muse_max_output_tokens: int = 8192

    jwt_secret: str = ""
    jwt_exp_seconds: int = 604800
    bcrypt_cost: int = 12
    password_min_len: int = 8
    code_exp_seconds: int = 600
    code_max_attempts: int = 3
    code_length: int = 6
    invite_exp_seconds: int = 259200
    seed_admin_email: str = ""
    seed_admin_password: str = ""
    auth_events_retention_days: int = 30

    resend_api_key: str = ""
    resend_from_email: str = ""
    resend_webhook_secret: str = ""
    public_app_url: str = ""

    apollo_enabled: bool = False
    apollo_api_key: str = ""
    apollo_rate_limit_rpm: int = 50
    apollo_api_base_url: str = "https://api.apollo.io/api/v1"

    calcom_api_key: str = ""
    calcom_event_type_id: str = ""
    calcom_api_base_url: str = "https://api.cal.com/v2"
    calcom_webhook_secret: str = ""
    calcom_public_booking_url: str = ""
    calcom_avail_days_ahead: int = 14
    calcom_avail_max_slots: int = 3

    rate_auth_limit: int = 5
    rate_global_limit: int = 60
    rate_window_seconds: int = 60

    target_approved: int = 30
    min_live_sources: int = 1
    max_attempts: int = 3
    tick_seconds: int = 5
    reconcile_every_ticks: int = 12
    llm_concurrency: int = 30
    http_concurrency: int = 3
    url_timeout_seconds: int = 5
    max_redirects: int = 5
    max_source_urls: int = 5
    lease_seconds: int = 300
    max_search_batch: int = 20
    exclusion_prompt_limit: int = 500

    memory_max_facts: int = 20
    memory_max_sources: int = 6
    email_max_words: int = 120
    reply_max_words: int = 150
    reply_context_window: int = 20
    draft_concurrency: int = 5
    send_concurrency: int = 3
    reply_concurrency: int = 10
    prompt_version: str = "ledgerwise-v1"
    icp_prompt: str = ""

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value):
        if value is None or value == "":
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    def validate_runtime(self) -> None:
        required = {
            "CLOUDFLARE_ACCOUNT_ID": self.cloudflare_account_id,
            "CLOUDFLARE_DATABASE_ID": self.cloudflare_database_id,
            "CLOUDFLARE_API_TOKEN": self.cloudflare_api_token,
            "API_TOKEN": self.api_token,
            "JWT_SECRET": self.jwt_secret,
            "SEED_ADMIN_EMAIL": self.seed_admin_email,
            "SEED_ADMIN_PASSWORD": self.seed_admin_password,
            "RESEND_API_KEY": self.resend_api_key,
            "RESEND_FROM_EMAIL": self.resend_from_email,
            "CALCOM_API_KEY": self.calcom_api_key,
            "CALCOM_EVENT_TYPE_ID": self.calcom_event_type_id,
        }
        missing = [name for name, value in required.items() if not value]
        if self.apollo_enabled and not self.apollo_api_key:
            missing.append("APOLLO_API_KEY")
        if missing and self.app_env.lower() == "production":
            raise RuntimeError("Missing required environment variables: " + ", ".join(missing))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
