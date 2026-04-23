import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Customer Feedback Backend")
    environment: str = os.getenv("ENVIRONMENT", "development")
    openapi_version: str = os.getenv("OPENAPI_VERSION", "3.1.0")


settings = Settings()
