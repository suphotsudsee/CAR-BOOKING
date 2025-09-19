"""
Application configuration settings
"""

from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


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

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()
