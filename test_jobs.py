import traceback
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token
import asyncio

print("Starting test client...")

async def main():
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3ODAyMjgwMjMsInN1YiI6IjZhMWMxN2QyMDZjN2M3NmYwM2RlNjY3MiIsInR5cGUiOiJhY2Nlc3MifQ.ofdewnbfoImAgS78SSIIRI47655A5fJjW46xsDDEY88"
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/jobs", headers={"Authorization": f"Bearer {token}"})
            print("Status code:", response.status_code)
            print("Response text:", response.text)
            
            response2 = client.get("/api/v1/companies", headers={"Authorization": f"Bearer {token}"})
            print("Companies Status:", response2.status_code)
    except Exception as e:
        print("Exception occurred:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
