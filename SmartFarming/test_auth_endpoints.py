#!/usr/bin/env python3
"""
Test authentication endpoints after FastAPI migration
Tests: Admin login, Farmer login, Buyer login
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("\n" + "="*60)
    print("TEST: Health Endpoint")
    print("="*60)
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

def test_admin_login():
    """Test admin login endpoint"""
    print("\n" + "="*60)
    print("TEST: Admin Login")
    print("="*60)
    try:
        payload = {
            "email": "gundesandeep2005@gmail.com",
            "password": "Sandy@7981"
        }
        response = requests.post(
            f"{BASE_URL}/api/admin-auth/login",
            json=payload
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_farmer_login():
    """Test farmer login endpoint"""
    print("\n" + "="*60)
    print("TEST: Farmer Login")
    print("="*60)
    try:
        payload = {
            "email": "farmer@smartfarming.com",
            "password": "password123"
        }
        response = requests.post(
            f"{BASE_URL}/api/auth/farmer-login",
            json=payload
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_buyer_login():
    """Test buyer login endpoint"""
    print("\n" + "="*60)
    print("TEST: Buyer Login")
    print("="*60)
    try:
        payload = {
            "phone": "+91-9876543210",
            "password": "password123"
        }
        response = requests.post(
            f"{BASE_URL}/api/buyer-auth/login",
            json=payload
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    print("Smart Farming Backend - Auth Endpoints Test")
    print("Testing FastAPI authentication endpoints...")
    
    # Test endpoints
    test_health()
    admin_resp = test_admin_login()
    farmer_resp = test_farmer_login()
    buyer_resp = test_buyer_login()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Admin Login: {'✓ OK' if admin_resp and admin_resp.status_code in [200, 401] else '✗ FAILED'}")
    print(f"Farmer Login: {'✓ OK' if farmer_resp and farmer_resp.status_code in [200, 401] else '✗ FAILED'}")
    print(f"Buyer Login: {'✓ OK' if buyer_resp and buyer_resp.status_code in [200, 401] else '✗ FAILED'}")
    print("\nExpected status codes: 200 (success), 401 (invalid credentials), NOT 404/500")
