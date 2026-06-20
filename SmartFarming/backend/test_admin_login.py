import requests
import json

url = "http://localhost:8000/api/auth/login"
data = {
    "email": "gundesandeep2005@gmail.com",
    "password": "Sandy@7981",
    "role": "admin"
}

try:
    response = requests.post(url, json=data, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
