#!/usr/bin/env python3
"""Test Render backend authentication endpoints"""

import requests
import json
import sys

BASE_URL = "https://smartfarming-marketplace.onrender.com"

def test_endpoint(name, method, endpoint, data=None):
    """Test a single endpoint"""
    try:
        url = f"{BASE_URL}{endpoint}"
        print(f"\n{'='*60}")
        print(f"Testing: {name}")
        print(f"{'='*60}")
        print(f"Endpoint: {method} {endpoint}")
        
        if method == "POST":
            response = requests.post(url, json=data)
        else:
            response = requests.get(url)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Body:")
        try:
            print(json.dumps(response.json(), indent=2))
        except:
            print(response.text[:500])
        
        return response.status_code
    except Exception as e:
        print(f"Error: {e}")
        return None

# Test endpoints
print("Testing Render Backend Endpoints")
print("=" * 60)

# Health check
health_status = test_endpoint("Health Check", "GET", "/api/health")

# Login endpoints
admin_status = test_endpoint("Admin Login", "POST", "/api/admin-auth/login", 
                           {"email": "admin@test.com", "password": "test"})

farmer_status = test_endpoint("Farmer Login", "POST", "/api/auth/farmer-login",
                            {"email": "farmer@test.com", "password": "test"})

buyer_status = test_endpoint("Buyer Login", "POST", "/api/buyer-auth/login",
                           {"phone": "9876543210", "password": "test"})

signup_status = test_endpoint("Generic Signup", "POST", "/api/auth/signup",
                            {"phone": "9876543210", "password": "test", "role": "farmer"})

print(f"\n{'='*60}")
print("Summary:")
print(f"{'='*60}")
print(f"Health:         {health_status} {'✓' if health_status == 200 else '✗'}")
print(f"Admin Login:    {admin_status} {'✓' if admin_status not in [404, None] else '✗'}")
print(f"Farmer Login:   {farmer_status} {'✓' if farmer_status not in [404, None] else '✗'}")
print(f"Buyer Login:    {buyer_status} {'✓' if buyer_status not in [404, None] else '✗'}")
print(f"Generic Signup: {signup_status} {'✓' if signup_status not in [404, None] else '✗'}")

# Check for 404s
if 404 in [admin_status, farmer_status, buyer_status, signup_status]:
    print("\n⚠️  Some endpoints returned 404 - routers may not be registered!")
    sys.exit(1)
else:
    print("\n✓ All endpoints are accessible (not 404)")
