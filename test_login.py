import requests

print("Testing login...")
response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    data={"username": "admin@corevita.co", "password": "adminpassword123"}
)
print("Status:", response.status_code)
print("Response:", response.text)
