import os
from dataclasses import dataclass, field
from typing import Any, Dict, List


def parse_openapi_servers() -> List[Dict[str, Any]]:
    url = os.getenv("OPENAPI_SERVER_URL", "http://localhost:8000")
    description = os.getenv("OPENAPI_SERVER_DESCRIPTION", "Local development server")
    return [{"url": url, "description": description}]


def parse_admin_bearer_token() -> str:
    configured_token = os.getenv("ADMIN_BEARER_TOKEN")
    if configured_token:
        return configured_token
    if os.getenv("ENVIRONMENT", "development") == "development":
        return "local-admin-token"
    return ""


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Customer Feedback Backend")
    environment: str = os.getenv("ENVIRONMENT", "development")
    openapi_version: str = os.getenv("OPENAPI_VERSION", "3.1.0")
    openapi_servers: List[Dict[str, Any]] = field(default_factory=parse_openapi_servers)
    admin_bearer_token: str = field(default_factory=parse_admin_bearer_token)


settings = Settings()
