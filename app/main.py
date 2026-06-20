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
    redirect_slashes=False,
)

# CORS — wildcard '*' is incompatible with allow_credentials=True,
# so we list allowed origins explicitly.
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "https://corevita.in",
    "https://www.corevita.in",
    "https://covian.in",
    "https://www.covian.in",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
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
