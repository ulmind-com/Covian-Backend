# 🚀 CoreVita Advisory Private Limited Backend

A scalable, production-grade, and enterprise-ready async MongoDB backend built with **Python 3.11+**, **FastAPI**, **MongoDB (Motor)**, and **Astral uv**. It follows **Clean Architecture** patterns to enforce strict separation of concerns, making it highly modular, maintainable, and customized for CoreVita Advisory Private Limited.

---

## 🌟 Key Features

*   **⚡ Speed & Modernity**: Managed using **Astral uv**—the ultra-fast Python package installer and resolver.
*   **🏗️ Clean Architecture**: Clear separation into API routing, business logic Services, database query Repositories, Pydantic schemas, and MongoDB models.
*   **🔒 Complete Security**:
    *   JWT Authentication with dual-token mechanics (**Access Tokens** and **Refresh Tokens**).
    *   Robust password hashing using the `bcrypt` algorithm.
    *   FastAPI dependency-injection-secured endpoint access.
*   **🗄️ Database Operations**:
    *   **Motor** async driver—the official high-performance asynchronous driver for MongoDB.
    *   Pydantic v2 document mapping for clean, validation-first database collections.
*   **🐳 Containerized Orchestration**: Production-ready, multi-stage `Dockerfile` and `docker-compose.yml` to spin up MongoDB and the API.
*   **🧪 Robust Testing**: Configured with `pytest` and `pytest-asyncio` utilizing an automated test database isolation fixture that clears collections between test runs to guarantee absolute test-state independence.
*   **📈 Settings Management**: Loaded dynamically from `.env` files using `pydantic-settings` v2.

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
│   │   ├── config.py            # Pydantic Settings, MongoDB URIs & CORS
│   │   └── security.py          # Password hashing & JWT operations
│   │
│   ├── db/                      # Database structure
│   │   ├── session.py           # Motor Client connection pool & get_db dependency
│   │   └── models/
│   │       └── user.py          # Pydantic MongoDB User Document Model
│   │
│   ├── schemas/                 # Data Transfer Objects (DTOs / Pydantic)
│   │   └── user.py              # Validation schemas for users & tokens
│   │
│   ├── services/                # Business logic layer
│   │   └── user_service.py      # Core logic (authentications, registrations)
│   │
│   ├── repositories/            # Database query encapsulation (CRUD)
│   │   └── user_repo.py         # Encapsulated MongoDB Motor CRUD operations
│   │
│   └── main.py                  # Entrypoint initializing FastAPI & CORS
│
├── tests/                       # Pytest integration & unit testing
│   ├── conftest.py              # Global fixtures (test database, async clients)
│   └── test_auth.py             # Auth flow integration tests
│
├── .env                         # Active local environment configurations
├── .env.example                 # Distributed template environment file
├── .gitignore                   # Standard git file ignores
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
3.  **Data Access Layer (`app/repositories`)**: Repositories abstract direct database interactions. They execute MongoDB Motor queries, decoupling the core application logic from the query mechanics.
4.  **Database Entities (`app/db/models`)**: Defines the document data schemas using Pydantic.
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
uv add motor

# Add a development dependency
uv add --dev pytest
```

### 2. Local Environment Setup

Create an active `.env` file by copying the distributed template:
```bash
cp .env.example .env
```
*(By default, the `.env` is pre-configured to look for a MongoDB server on `mongodb+srv://...` for seamless runs).*

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
1.  A MongoDB database container on port `27017` with a persistent docker volume.
2.  Our minimal FastAPI app container exposed on port `8000`.

---

## 🧪 Testing

Testing is run using `pytest` and `pytest-asyncio`. 

We implement automated test database isolation inside `tests/conftest.py`:
*   Before the test session starts, a temporary database `test_project_form_prem` is dropped/created.
*   Between individual test runs, collections are emptied automatically.
*   This keeps tests 100% isolated, reliable, and extremely fast.

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
