# Inputs: process environment variables and optional .env values, including configured Muse input, output, and web-search prices.
# Outputs: Settings, get_settings(), validated runtime configuration, and parsed CORS origins.
# Explanation: Centralizes runtime configuration and the user-supplied pricing schedule used for token and web-search cost accounting.
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False)

    app_env: str = "production"
    cors_origins: str = "https://ledgerwise-frontend.vercel.app"

    cloudflare_account_id: str = "ad2f9bcb89b0518e9160277fa7467f8d"
    cloudflare_database_id: str = "4dfb5080-1a5a-4725-8bc5-43614cefcdcb"
    cloudflare_api_token: str = ""
    d1_api_base_url: str = "https://api.cloudflare.com/client/v4"

    api_token: str = ""
    muse_api_base_url: str = "https://api.meta.ai/v1"
    muse_model: str = "muse-ember-1.0"
    muse_reasoning_effort: str = "medium"
    muse_max_output_tokens: int = 8192
    muse_input_price_per_million_usd: float | None = Field(default=0.10, ge=0)
    muse_output_price_per_million_usd: float | None = Field(default=0.50, ge=0)
    muse_search_price_per_thousand_usd: float | None = Field(default=2.50, ge=0)
    muse_pricing_version: str | None = "user-supplied-2026-11-16-v1"

    jwt_secret: str = ""
    jwt_exp_seconds: int = 604800
    bcrypt_cost: int = 12
    password_min_len: int = 8
    code_exp_seconds: int = 600
    code_max_attempts: int = 3
    code_length: int = 6
    invite_exp_seconds: int = 259200
    seed_admin_email: str = "alphaspex@gmail.com"
    seed_admin_password: str = ""
    auth_events_retention_days: int = 30

    resend_api_key: str = ""
    resend_from_email: str = "onboarding@resend.dev"
    resend_webhook_secret: str = ""
    resend_inbound_domain: str = ""
    public_app_url: str = "https://ledgerwise-frontend.vercel.app"

    apollo_enabled: bool = False
    apollo_api_key: str = ""
    apollo_rate_limit_rpm: int = 50
    apollo_api_base_url: str = "https://api.apollo.io/api/v1"

    calcom_api_key: str = ""
    calcom_event_type_id: str = "7921907"
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

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

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
