from fastapi import APIRouter
from app.api.v1.endpoints import auth, health, user

api_router = APIRouter()

# Register sub-routers under appropriate prefixes and swagger tag categories
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(user.router, prefix="/users", tags=["Users"])
api_router.include_router(health.router, prefix="/health", tags=["System Health"])
