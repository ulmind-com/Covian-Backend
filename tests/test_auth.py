import pytest
from httpx import AsyncClient

# Use the standard pytest-asyncio marker to enable async tests
pytestmark = pytest.mark.asyncio


async def test_health_check(client: AsyncClient) -> None:
    """
    Test the health check endpoint returns 200 and correct status.
    """
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "environment" in data


async def test_user_registration_and_login_flow(client: AsyncClient) -> None:
    """
    Test a complete user cycle:
    1. Register a new user.
    2. Attempt registering with the same email (should fail).
    3. Login with credentials to obtain JWT access & refresh tokens.
    4. Query protected profile endpoint using the access token.
    5. Query protected profile without headers (should fail).
    """
    email = "testuser@example.com"
    password = "supersecurepassword123"
    name = "Test User"

    # --- 1. Register ---
    register_payload = {
        "email": email,
        "password": password,
        "name": name
    }
    response = await client.post("/api/v1/auth/register", json=register_payload)
    assert response.status_code == 201
    user_data = response.json()
    assert user_data["email"] == email
    assert user_data["name"] == name
    assert "id" in user_data
    assert "hashed_password" not in user_data  # Hashed password must never be exposed!

    # --- 2. Duplicate Register ---
    dup_response = await client.post("/api/v1/auth/register", json=register_payload)
    assert dup_response.status_code == 400
    assert "registered" in dup_response.json()["detail"].lower()

    # --- 3. Login ---
    # Login expects application/x-www-form-urlencoded as per OAuth2 specifications
    login_data = {
        "username": email,
        "password": password
    }
    login_response = await client.post("/api/v1/auth/login", data=login_data)
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert token_data["token_type"] == "bearer"
    
    access_token = token_data["access_token"]
    refresh_token = token_data["refresh_token"]

    # --- 4. Get Current User Profile (Authenticated) ---
    headers = {"Authorization": f"Bearer {access_token}"}
    profile_response = await client.get("/api/v1/users/me", headers=headers)
    assert profile_response.status_code == 200
    profile_data = profile_response.json()
    assert profile_data["email"] == email
    assert profile_data["name"] == name

    # --- 5. Get Profile Unauthorized (No Headers) ---
    unauth_response = await client.get("/api/v1/users/me")
    assert unauth_response.status_code == 401
    
    # --- 6. Refresh Token flow ---
    refresh_payload = {"refresh_token": refresh_token}
    refresh_response = await client.post("/api/v1/auth/refresh", json=refresh_payload)
    assert refresh_response.status_code == 200
    new_token_data = refresh_response.json()
    assert "access_token" in new_token_data
    assert "refresh_token" in new_token_data
