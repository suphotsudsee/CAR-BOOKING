"""Application configuration settings."""

from typing import Any, List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings.sources import (
    DotEnvSettingsSource,
    EnvSettingsSource,
    PydanticBaseSettingsSource,
)


class _SafeEnvSettingsSource(EnvSettingsSource):
    """Environment settings source with tolerant JSON decoding."""

    def decode_complex_value(self, field_name: str, field: Any, value: Any) -> Any:  # type: ignore[override]
        if isinstance(value, str) and not value.strip():
            return value
        try:
            return super().decode_complex_value(field_name, field, value)
        except ValueError:
            return value


class _SafeDotEnvSettingsSource(_SafeEnvSettingsSource, DotEnvSettingsSource):
    """DotEnv settings source that reuses the safe JSON decoding."""


class Settings(BaseSettings):
    """Application settings"""

    # Application
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=True)
    ENABLE_API_DOCS: bool = Field(default=True)
    SECRET_KEY: str = Field(default="change-me-in-production")
    API_V1_STR: str = Field(default="/api/v1")

    # Authentication
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)
    ALGORITHM: str = Field(default="HS256")

    # Database
    DATABASE_URL: str = Field(
        default="mysql+aiomysql://vehicle_user:vehicle_password@localhost:3306/vehicle_booking"
    )

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    # Email
    EMAIL_HOST: Optional[str] = Field(default=None)
    EMAIL_PORT: int = Field(default=587)
    EMAIL_USERNAME: Optional[str] = Field(default=None)
    EMAIL_PASSWORD: Optional[str] = Field(default=None)
    EMAIL_FROM: Optional[str] = Field(default=None)
    EMAIL_FROM_NAME: str = Field(default="Office Vehicle Booking System")
    EMAIL_USE_TLS: bool = Field(default=True)

    # LINE Notify
    LINE_NOTIFY_TOKEN: Optional[str] = Field(default=None)

    # File Upload
    UPLOAD_DIR: str = Field(default="uploads")
    MAX_FILE_SIZE: int = Field(default=10485760)  # 10MB
    ALLOWED_EXTENSIONS: List[str] = Field(default=["jpg", "jpeg", "png", "pdf"])
    IMAGE_MAX_DIMENSION: int = Field(default=1920)
    IMAGE_PREVIEW_DIMENSION: int = Field(default=640)

    # Object storage (S3 compatible)
    S3_ENDPOINT_URL: Optional[str] = Field(default=None)
    S3_ACCESS_KEY_ID: Optional[str] = Field(default=None)
    S3_SECRET_ACCESS_KEY: Optional[str] = Field(default=None)
    S3_REGION_NAME: str = Field(default="us-east-1")
    S3_BUCKET_NAME: str = Field(default="vehicle-booking-uploads")
    S3_SIGNATURE_VERSION: Optional[str] = Field(default="s3v4")
    S3_FORCE_PATH_STYLE: bool = Field(default=True)
    S3_URL_EXPIRATION: int = Field(default=900)  # 15 minutes

    # Celery
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/2")

    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(default="json")

    # CORS
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"]
    )
    ALLOWED_HOSTS: Optional[List[str]] = Field(default=None)

    # Pagination
    DEFAULT_PAGE_SIZE: int = Field(default=20)
    MAX_PAGE_SIZE: int = Field(default=100)

    @field_validator("ALLOWED_EXTENSIONS", mode="before")
    @classmethod
    def _parse_allowed_extensions(cls, value: Optional[List[str] | str]) -> Optional[List[str]]:
        """Allow comma separated values in environment configuration."""
        if value is None or isinstance(value, list):
            return value
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return []
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def _parse_allowed_origins(cls, value: Optional[List[str] | str]) -> Optional[List[str]]:
        """Allow comma separated CORS origins in environment configuration."""
        if value is None or isinstance(value, list):
            return value
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return []
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        env_ignore_empty=True,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: EnvSettingsSource,
        dotenv_settings: DotEnvSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Use safe sources that gracefully handle invalid JSON values."""

        return (
            init_settings,
            _SafeEnvSettingsSource(settings_cls),
            _SafeDotEnvSettingsSource(settings_cls),
            file_secret_settings,
        )

# Create settings instance
settings = Settings()

