import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.core.config import settings

from app.db.mongo import init_db

logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Asynchronous context manager to manage application lifecycle events
    (startup and shutdown).
    """
    logger.info("Starting up the FastAPI application...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Initializing Beanie ODM with MongoDB client...")
    try:
        await init_db()
        logger.info("Successfully connected to MongoDB and initialized Beanie ODM.")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB / init Beanie: {e}")
        raise e
    yield
    logger.info("Shutting down the FastAPI application...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Set up CORS middleware to allow all origins for now to fix deployment issues
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include core versioned routing
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
async def root_redirect():
    """
    Root endpoint redirecting or pointing to Swagger UI documentation.
    """
    return {
        "message": f"Welcome to the {settings.PROJECT_NAME}!",
        "docs_url": "/docs",
        "health_check_url": f"{settings.API_V1_STR}/health",
    }
