from typing import Dict
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("", response_model=Dict[str, str])
async def health_check() -> Dict[str, str]:
    """
    Service health check endpoint.
    Returns status and current runtime environment.
    """
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "api_version": "v1"
    }
