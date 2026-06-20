import logging
from typing import Any, Dict, List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Configure basic logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    PROJECT_NAME: str = "CoreVita Advisory Private Limited"
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] | str = ["http://localhost:3000", "http://localhost:8000"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database & Redis
    MONGODB_URL: str = "mongodb+srv://samiran:samiran2004@cluster2004.eowyegm.mongodb.net/project_form_prem"
    MONGODB_DB_NAME: str = "project_form_prem"
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT Security
    # In production, change these to highly secure keys!
    JWT_SECRET_KEY: str = "supersecretaccesskeyforfastapiproductionstarter123!"
    JWT_REFRESH_SECRET_KEY: str = "supersecretrefreshkeyforfastapiproductionstarter123!"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30       # 30 minutes
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""


settings = Settings()
