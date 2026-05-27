# 🚀 Premium FastAPI Backend Starter Template

A scalable, production-grade, and enterprise-ready backend starter template built with **Python 3.11+**, **FastAPI**, **SQLAlchemy 2.0**, and **Astral uv**. It follows **Clean Architecture** patterns to enforce strict separation of concerns, making it highly modular, maintainable, and ready for real client work.

---

## 🌟 Key Features

*   **⚡ Speed & Modernity**: Managed using **Astral uv**—the ultra-fast Python package installer and resolver.
*   **🏗️ Clean Architecture**: Clear separation into API routing, business logic Services, database query Repositories, Pydantic schemas, and SQLAlchemy database models.
*   **🔒 Complete Security**:
    *   JWT Authentication with dual-token mechanics (**Access Tokens** and **Refresh Tokens**).
    *   Robust password hashing using the `bcrypt` algorithm.
    *   FastAPI dependency-injection-secured endpoint access.
*   **🗄️ Database Operations**:
    *   **SQLAlchemy 2.0** async engine with modern type annotations (`Mapped`, `mapped_column`).
    *   Async database driver (`asyncpg`) for native asynchronous PostgreSQL operations.
    *   Full **Alembic** migrations setup configured dynamically using the app's settings.
*   **🐳 Containerized Orchestration**: Production-ready, multi-stage `Dockerfile` and `docker-compose.yml` to spin up PostgreSQL and the API.
*   **🧪 Robust Testing**: Configured with `pytest` and `pytest-asyncio` utilizing the **transactional test pattern** to run tests instantly in isolated database sessions that roll back automatically.
*   **📈 Settings Management**: Loaded dynamically from `.env` files using `pydantic-settings` v2 with dynamic database URI building.

---

## 📁 Project Directory Structure

```text
Project_For_Prem_Backend/
│
├── app/
│   ├── api/                     # API routes & endpoint controllers
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── auth.py      # Registration, Login, and Token Refresh
│   │   │   │   ├── user.py      # User profile retrieval (/me, /{id})
│   │   │   │   └── health.py    # System health checks
│   │   │   └── router.py        # Consolidation of all v1 routes
│   │   └── deps.py              # Injectable dependencies (Database, Auth)
│   │
│   ├── core/                    # Core configs & security logic
│   │   ├── config.py            # Pydantic Settings, dynamic DB URIs & CORS
│   │   └── security.py          # Password hashing & JWT operations
│   │
│   ├── db/                      # Database structure
│   │   ├── base.py              # Declarative base & Alembic registry
│   │   ├── session.py           # Async engine & get_db generator
│   │   └── models/
│   │       └── user.py          # SQLAlchemy User model (UUID, timestamped)
│   │
│   ├── schemas/                 # Data Transfer Objects (DTOs / Pydantic)
│   │   └── user.py              # Validation schemas for users & tokens
│   │
│   ├── services/                # Business logic layer
│   │   └── user_service.py      # Core logic (authentications, registrations)
│   │
│   ├── repositories/            # Database query encapsulation (CRUD)
│   │   └── user_repo.py         # Encapsulated SQLAlchemy DB selects & inserts
│   │
│   └── main.py                  # Entrypoint initializing FastAPI & CORS
│
├── migrations/                  # Alembic DB migration files
├── tests/                       # Pytest integration & unit testing
│   ├── conftest.py              # Global fixtures (test database, async clients)
│   └── test_auth.py             # Auth flow integration tests
│
├── .env                         # Active local environment configurations
├── .env.example                 # Distributed template environment file
├── .gitignore                   # Standard git file ignores
├── alembic.ini                  # Alembic DB configuration
├── Dockerfile                   # Multi-stage optimized app container
├── docker-compose.yml           # Database + API container coordinator
├── pyproject.toml               # Python project dependencies manifest
└── README.md                    # Project walkthrough & documentation
```

---

## 🛠️ Architecture & Separation of Concerns

This project implements the **clean architecture** paradigm to keep database, routing, and business operations strictly isolated from one another:

1.  **Request Layer (`app/api`)**: Routes are cleanly structured and versioned (e.g., `/api/v1`). They use FastAPI dependencies (`app/api/deps.py`) to inject security checks and database sessions, offloading requests straight to the Service layer.
2.  **Business Logic Layer (`app/services`)**: Services represent the central domain engine. They do not query databases directly; instead, they command repositories. Hashing and business rules (like uniqueness validations) live entirely here.
3.  **Data Access Layer (`app/repositories`)**: Repositories abstract direct database interactions. They execute SQLAlchemy queries, decoupling the core application logic from the query mechanics.
4.  **Database Entities (`app/db/models`)**: Defines the physical data layouts using SQLAlchemy.
5.  **Data Transfer Objects (`app/schemas`)**: Pydantic v2 schemas act as strong typing boundaries to filter and validate request data entering the API, and sanitizing output data before leaving the server (e.g. automatically stripping `hashed_password`).

---

## 🚀 Quick Start Guide

### Prerequisites

Ensure you have **uv** installed in your system:
```bash
# On Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 1. Project Initialization

To sync all dependencies and activate the virtual environment, run:
```bash
# Sync dependencies and create a virtualenv (.venv) automatically
uv sync
```

To manually add or remove packages in the future:
```bash
# Add a production dependency
uv add fastapi

# Add a development dependency
uv add --dev pytest
```

### 2. Local Environment Setup

Create an active `.env` file by copying the distributed template:
```bash
cp .env.example .env
```
*(By default, the `.env` is pre-configured to look for a PostgreSQL server on `localhost:5432` for seamless local runs).*

---

## 🗄️ Database Migrations (Alembic)

Database schema alterations are managed with Alembic.

### Generate an Autogenerated Migration:
```bash
# This command automatically detects model schema updates
uv run alembic revision --autogenerate -message "init user table"
```

### Apply All Pending Migrations:
```bash
uv run alembic upgrade head
```

### Rollback a Migration:
```bash
uv run alembic downgrade -1
```

---

## 🏃 Running the Application

Start the FastAPI application in hot-reload development mode:
```bash
uv run uvicorn app.main:app --reload
```
Once booted, the following URLs will be active:
*   **🚀 API Base Server**: `http://127.0.0.1:8000`
*   **📖 Swagger Interactive Docs**: `http://127.0.0.1:8000/docs`
*   **📊 Redoc Structured Docs**: `http://127.0.0.1:8000/redoc`

---

## 🐳 Docker Deployment

The project can be entirely run inside container environments.

### Spin up database and backend API:
```bash
docker compose up -d --build
```
This starts:
1.  A PostgreSQL database container named `premium_postgres_db` on port `5432` with a persistent docker volume.
2.  Our minimal FastAPI app container named `premium_fastapi_web` exposed on port `8000`.

*Note: The FastAPI container automatically waits for PostgreSQL's internal health check to succeed before initiating boot, preventing connection retry exceptions.*

---

## 🧪 Testing

Testing is run using `pytest` and `pytest-asyncio`. 

We implement the **transactional test pattern** inside `tests/conftest.py`:
*   Every test receives an `AsyncSession` that is already in an active transaction.
*   Upon test completion, the fixture automatically triggers a `rollback()`.
*   This keeps tests 100% isolated and extremely fast as no permanent disk modifications are committed.

To run the full suite:
```bash
uv run pytest
```

---

## 🔒 API Endpoints Specifications

### System Health
*   **`GET /api/v1/health`**: Simple status endpoint to check server availability.

### Authentication
*   **`POST /api/v1/auth/register`**: Register a new user account.
    *   **Body**: `{ "email": "user@example.com", "password": "securepassword", "name": "John Doe" }`
    *   **Response**: `201 Created` with User object (password omitted).
*   **`POST /api/v1/auth/login`**: Authenticate and retrieve token pairs.
    *   **Body**: `x-www-form-urlencoded` fields `username` and `password`.
    *   **Response**: `200 OK` with JSON `{ "access_token": "...", "refresh_token": "...", "token_type": "bearer" }`.
*   **`POST /api/v1/auth/refresh`**: Refresh an expired access token using a valid refresh token.
    *   **Body**: `{ "refresh_token": "..." }`
    *   **Response**: `200 OK` with new access and refresh token pair.

### Users (Protected Endpoints)
*   **`GET /api/v1/users/me`**: Fetch profile details of the currently logged-in active user.
    *   **Headers**: `Authorization: Bearer <access_token>`
*   **`GET /api/v1/users/{id}`**: Fetch user details by their database UUID.
    *   **Headers**: `Authorization: Bearer <access_token>`
