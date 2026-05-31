import traceback
from fastapi.testclient import TestClient
from app.main import app

print("Starting test client...")
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3ODAyMjgwMjMsInN1YiI6IjZhMWMxN2QyMDZjN2M3NmYwM2RlNjY3MiIsInR5cGUiOiJhY2Nlc3MifQ.ofdewnbfoImAgS78SSIIRI47655A5fJjW46xsDDEY88"

try:
    with TestClient(app) as client:
        response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
        print("Status code:", response.status_code)
        print("Response text:", response.text)
except Exception as e:
    print("Exception occurred:")
    traceback.print_exc()
