FROM python:3.11-slim AS builder

# Copy uv binary from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Compile Python bytecode for faster startup times inside the container
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app

# Copy pyproject.toml to load dependencies
COPY pyproject.toml /app/

# Sync virtualenv and install dependencies
# We use uv to create a virtual environment and populate it from pyproject.toml
RUN --mount=type=cache,target=/root/.cache/uv \
    uv venv /app/.venv && \
    . /app/.venv/bin/activate && \
    uv pip install -r pyproject.toml


# ==============================================================================
# STAGE 2: Lightweight runtime stage
# ==============================================================================
FROM python:3.11-slim

WORKDIR /app

# Copy the pre-compiled virtual environment from the builder
COPY --from=builder /app/.venv /app/.venv

# Inject the virtual environment bin folder into the PATH
ENV PATH="/app/.venv/bin:$PATH"

# Ensure print logs are immediately flushed to docker output
ENV PYTHONUNBUFFERED=1

# Copy application files
COPY app /app/app
COPY migrations /app/migrations
COPY alembic.ini /app/alembic.ini

# Expose default FastAPI port
EXPOSE 8000

# Run FastAPI app with high performance uvicorn production config
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
