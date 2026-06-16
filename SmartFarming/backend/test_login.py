"""Quick test of all login endpoints"""
import requests
import json

BASE = "http://localhost:8000/api"

print("=" * 50)
print("  SMART FARMING - LOGIN TEST")
print("=" * 50)

# Test 1: Health check
print("\n[1] Health Check")
try:
    r = requests.get(f"{BASE}/health")
    print(f"    Status: {r.status_code} - {r.json()}")
    print(f"    Result: PASS" if r.status_code == 200 else "    Result: FAIL")
except Exception as e:
    print(f"    ERROR: Backend not running! Start with: python app.py")
    exit()

# Test 2: Admin Login
print("\n[2] Admin Login (email: gundesandeep2005@gmail.com)")
r = requests.post(f"{BASE}/admin-auth/login", json={
    "email": "gundesandeep2005@gmail.com",
    "password": "Sandy@7981"
})
data = r.json()
has_token = "token" in data
has_user = "user" in data
has_role = data.get("user", {}).get("role") == "admin"
print(f"    Status: {r.status_code}")
print(f"    Has 'token': {has_token}")
print(f"    Has 'user': {has_user}")
if has_user:
    print(f"    user.name: {data['user']['name']}")
    print(f"    user.role: {data['user']['role']}")
passed = r.status_code == 200 and has_token and has_user and has_role
print(f"    Result: {'PASS' if passed else 'FAIL'}")

# Test 3: Farmer Login endpoint
print("\n[3] Farmer Login Endpoint (/auth/farmer-login)")
r = requests.post(f"{BASE}/auth/farmer-login", json={
    "email": "test@test.com",
    "password": "testpass"
})
endpoint_exists = r.status_code != 404
print(f"    Status: {r.status_code}")
print(f"    Endpoint exists: {endpoint_exists}")
print(f"    Response: {r.json().get('message', '')}")
print(f"    Result: {'PASS' if endpoint_exists else 'FAIL'}")

# Test 4: Buyer Login endpoint
print("\n[4] Buyer Login Endpoint (/buyer-auth/login)")
r = requests.post(f"{BASE}/buyer-auth/login", json={
    "phone": "1234567890",
    "password": "testpass"
})
endpoint_exists = r.status_code != 404
print(f"    Status: {r.status_code}")
print(f"    Endpoint exists: {endpoint_exists}")
print(f"    Response: {r.json().get('error', r.json().get('message', ''))}")
print(f"    Result: {'PASS' if endpoint_exists else 'FAIL'}")

# Test 5: Farmer Signup endpoint
print("\n[5] Farmer Signup Endpoint (/auth/signup)")
r = requests.post(f"{BASE}/auth/signup", json={
    "phone": "0000000000",
    "password": "x"
})
endpoint_exists = r.status_code != 404
print(f"    Status: {r.status_code}")
print(f"    Endpoint exists: {endpoint_exists}")
print(f"    Result: {'PASS' if endpoint_exists else 'FAIL'}")

print("\n" + "=" * 50)
print("  ALL TESTS COMPLETE")
print("=" * 50)
