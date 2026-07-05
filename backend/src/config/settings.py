"""
SBI Vishwas — Configuration Settings

Pydantic Settings class that loads and validates all environment variables.
Every external dependency is configurable — no hardcoded values.
"""

from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Application environment."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class AIProvider(str, Enum):
    """Supported AI providers."""
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"


class StorageProvider(str, Enum):
    """Supported storage backends."""
    LOCAL = "local"
    S3 = "s3"
    GCS = "gcs"


class SMSProvider(str, Enum):
    """Supported SMS providers."""
    TWILIO = "twilio"
    MSG91 = "msg91"
    AWS_SNS = "aws_sns"


class EmailProvider(str, Enum):
    """Supported email providers."""
    SMTP = "smtp"
    SENDGRID = "sendgrid"
    SES = "ses"


class Settings(BaseSettings):
    """
    Central configuration for SBI Vishwas.

    All values are loaded from environment variables with sensible defaults
    for development. Production deployments MUST set all required values.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -------------------------------------------------------------------------
    # Application
    # -------------------------------------------------------------------------
    app_name: str = "sbi-vishwas"
    app_env: Environment = Environment.DEVELOPMENT
    app_debug: bool = False
    app_version: str = "1.0.0"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_workers: int = 4
    app_log_level: str = "INFO"
    app_secret_key: str = Field(default="CHANGE-ME-IN-PRODUCTION", min_length=16)
    app_cors_origins: str = "http://localhost:3000,http://localhost:8000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.app_cors_origins.split(",")]

    @property
    def is_development(self) -> bool:
        return self.app_env == Environment.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        return self.app_env == Environment.PRODUCTION

    # -------------------------------------------------------------------------
    # Database — PostgreSQL
    # -------------------------------------------------------------------------
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "sbi_vishwas"
    database_user: str = "vishwas"
    database_password: str = "vishwas_dev_password"
    database_ssl_mode: str = "prefer"
    database_pool_size: int = 20
    database_max_overflow: int = 10
    database_echo: bool = False
    database_url: str | None = None

    @property
    def async_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+asyncpg://{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}"
        )

    @property
    def sync_database_url(self) -> str:
        return (
            f"postgresql://{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}"
        )

    # -------------------------------------------------------------------------
    # Redis
    # -------------------------------------------------------------------------
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = "vishwas_redis_dev"
    redis_db: int = 0
    redis_ssl: bool = False
    redis_url: str | None = None

    @property
    def redis_connection_url(self) -> str:
        if self.redis_url:
            return self.redis_url
        protocol = "rediss" if self.redis_ssl else "redis"
        return f"{protocol}://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # Celery
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None

    @property
    def celery_broker(self) -> str:
        if self.celery_broker_url:
            return self.celery_broker_url
        return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/1"

    @property
    def celery_backend(self) -> str:
        if self.celery_result_backend:
            return self.celery_result_backend
        return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/2"

    # -------------------------------------------------------------------------
    # Qdrant — Vector Database
    # -------------------------------------------------------------------------
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_grpc_port: int = 6334
    qdrant_api_key: str | None = None
    qdrant_collection_name: str = "sbi_vishwas_knowledge"
    qdrant_memory_collection: str = "sbi_vishwas_memory"
    qdrant_vector_size: int = 768

    # -------------------------------------------------------------------------
    # AI Providers
    # -------------------------------------------------------------------------
    ai_default_provider: AIProvider = AIProvider.GEMINI
    ai_default_model: str = "gemini-2.5-flash"
    ai_temperature: float = 0.1
    ai_max_tokens: int = 4096
    ai_timeout_seconds: int = 60
    ai_max_retries: int = 3

    # Gemini
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    gemini_embedding_model: str = "text-embedding-004"

    # OpenAI
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_org_id: str | None = None

    # Anthropic
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-20250514"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"
    ollama_embedding_model: str = "nomic-embed-text"

    # Embedding
    embedding_provider: AIProvider = AIProvider.GEMINI
    embedding_model: str = "text-embedding-004"
    embedding_dimensions: int = 768
    embedding_batch_size: int = 100

    # -------------------------------------------------------------------------
    # JWT / Auth
    # -------------------------------------------------------------------------
    jwt_secret_key: str = Field(default="CHANGE-ME-JWT-SECRET", min_length=16)
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    jwt_issuer: str = "sbi-vishwas"

    # OAuth
    oauth_provider: str | None = None
    oauth_client_id: str | None = None
    oauth_client_secret: str | None = None
    oauth_redirect_uri: str | None = None

    # -------------------------------------------------------------------------
    # Encryption
    # -------------------------------------------------------------------------
    encryption_key: str | None = None
    pii_encryption_key: str | None = None

    # -------------------------------------------------------------------------
    # Email / SMTP
    # -------------------------------------------------------------------------
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = True
    smtp_from_email: str = "noreply@sbi.co.in"
    smtp_from_name: str = "SBI Vishwas"
    email_provider: EmailProvider = EmailProvider.SMTP
    sendgrid_api_key: str | None = None

    # -------------------------------------------------------------------------
    # SMS
    # -------------------------------------------------------------------------
    sms_provider: str | None = None
    sms_from_number: str | None = None
    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    msg91_auth_key: str | None = None
    msg91_sender_id: str | None = None

    # -------------------------------------------------------------------------
    # WhatsApp
    # -------------------------------------------------------------------------
    whatsapp_provider: str | None = None
    whatsapp_api_url: str | None = None
    whatsapp_api_token: str | None = None
    whatsapp_phone_number_id: str | None = None
    whatsapp_business_account_id: str | None = None
    whatsapp_verify_token: str | None = None

    # -------------------------------------------------------------------------
    # OCR
    # -------------------------------------------------------------------------
    ocr_provider: str | None = None
    google_vision_credentials_path: str | None = None

    # -------------------------------------------------------------------------
    # CBS (Core Banking System)
    # -------------------------------------------------------------------------
    cbs_base_url: str | None = None
    cbs_api_key: str | None = None
    cbs_api_secret: str | None = None
    cbs_timeout_seconds: int = 30
    cbs_max_retries: int = 3

    # -------------------------------------------------------------------------
    # KYC
    # -------------------------------------------------------------------------
    kyc_provider: str | None = None
    kyc_api_url: str | None = None
    kyc_api_key: str | None = None
    kyc_api_secret: str | None = None

    # -------------------------------------------------------------------------
    # GST
    # -------------------------------------------------------------------------
    gst_api_url: str | None = None
    gst_api_key: str | None = None

    # -------------------------------------------------------------------------
    # Account Aggregator
    # -------------------------------------------------------------------------
    aa_base_url: str | None = None
    aa_client_id: str | None = None
    aa_client_secret: str | None = None

    # -------------------------------------------------------------------------
    # Storage
    # -------------------------------------------------------------------------
    storage_provider: StorageProvider = StorageProvider.LOCAL
    storage_local_path: str = "./storage"
    aws_s3_bucket: str | None = None
    aws_s3_region: str | None = None
    aws_s3_access_key: str | None = None
    aws_s3_secret_key: str | None = None
    gcs_bucket: str | None = None
    gcs_credentials_path: str | None = None

    # -------------------------------------------------------------------------
    # Kafka
    # -------------------------------------------------------------------------
    kafka_enabled: bool = False
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic_banking_events: str = "banking.events"
    kafka_topic_agent_events: str = "agent.events"
    kafka_topic_notifications: str = "notifications"
    kafka_topic_audit: str = "audit.log"

    # -------------------------------------------------------------------------
    # Observability
    # -------------------------------------------------------------------------
    otel_enabled: bool = True
    otel_service_name: str = "sbi-vishwas"
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    prometheus_enabled: bool = True
    log_format: str = "json"
    log_file_path: str = "./logs/sbi-vishwas.log"

    # -------------------------------------------------------------------------
    # Rate Limiting
    # -------------------------------------------------------------------------
    rate_limit_enabled: bool = True
    rate_limit_default: str = "100/minute"
    rate_limit_auth: str = "10/minute"
    rate_limit_ai: str = "30/minute"

    # -------------------------------------------------------------------------
    # SBI-Specific Configuration
    # -------------------------------------------------------------------------
    sbi_branch_code: str | None = None
    sbi_region_code: str | None = None
    sbi_ifsc_prefix: str = "SBIN"

    # SLA (in hours)
    sla_complaint_acknowledgment: int = 1
    sla_complaint_resolution: int = 168  # 7 days
    sla_escalation_level1: int = 48
    sla_escalation_level2: int = 96
    sla_escalation_ombudsman: int = 336  # 14 days

    # Agent Configuration
    agent_default_confidence_threshold: float = 0.85
    agent_max_iterations: int = 10
    agent_timeout_seconds: int = 120
    agent_human_approval_required: bool = True

    # Dormancy Configuration
    dormancy_inactive_months: int = 24
    dormancy_scan_batch_size: int = 1000
    dormancy_readiness_threshold: float = 0.70

    # Credit Readiness
    credit_readiness_min_score: float = 0.65
    credit_max_ticket_size: int = 50000
    credit_approval_required: bool = True

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """Ensure critical settings are configured for production."""
        if self.app_env == Environment.PRODUCTION:
            if self.app_secret_key == "CHANGE-ME-IN-PRODUCTION":
                raise ValueError("APP_SECRET_KEY must be changed for production")
            if self.jwt_secret_key == "CHANGE-ME-JWT-SECRET":
                raise ValueError("JWT_SECRET_KEY must be changed for production")
            if not self.encryption_key:
                raise ValueError("ENCRYPTION_KEY is required for production")
            if not self.pii_encryption_key:
                raise ValueError("PII_ENCRYPTION_KEY is required for production")
        return self


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.

    Uses lru_cache so the Settings object is created once and reused.
    """
    return Settings()
