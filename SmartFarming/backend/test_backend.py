"""
Comprehensive Backend Testing Suite for Smart Farmer Marketplace
Tests for all API endpoints and core functionality
"""

import pytest
import json
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app, mysql
from models.models import User, Farmer, Buyer, Product, Order, Payment

@pytest.fixture
def client():
    """Flask test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def auth_headers(client):
    """Get JWT authentication headers"""
    # Register and login test user
    register_response = client.post(
        '/api/auth/register',
        json={
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'first_name': 'Test',
            'last_name': 'User',
            'phone': '9876543210',
            'role': 'buyer'
        }
    )
    
    token = register_response.json['data']['access_token']
    return {'Authorization': f'Bearer {token}'}

# ============================================================================
# HEALTH & INFO ENDPOINTS
# ============================================================================

class TestHealthEndpoints:
    """Test health check and info endpoints"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.json
        assert data['status'] == 'success'
    
    def test_api_info(self, client):
        """Test API info endpoint"""
        response = client.get('/api')
        assert response.status_code == 200
        data = response.json
        assert 'endpoints' in data

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

class TestAuthenticationEndpoints:
    """Test all authentication endpoints"""
    
    def test_register_farmer(self, client):
        """Test farmer registration"""
        response = client.post(
            '/api/auth/register',
            json={
                'email': 'farmer@test.com',
                'password': 'FarmerPass123!',
                'first_name': 'John',
                'last_name': 'Farmer',
                'phone': '9876543210',
                'role': 'farmer'
            }
        )
        
        assert response.status_code == 201
        data = response.json
        assert data['status'] == 'success'
        assert 'access_token' in data['data']
        assert 'refresh_token' in data['data']
        assert data['data']['user']['role'] == 'farmer'
    
    def test_register_buyer(self, client):
        """Test buyer registration"""
        response = client.post(
            '/api/auth/register',
            json={
                'email': 'buyer@test.com',
                'password': 'BuyerPass123!',
                'first_name': 'Jane',
                'last_name': 'Buyer',
                'phone': '9876543211',
                'role': 'buyer'
            }
        )
        
        assert response.status_code == 201
        data = response.json
        assert data['data']['user']['role'] == 'buyer'
    
    def test_register_duplicate_email(self, client):
        """Test registration with duplicate email"""
        # First registration
        client.post(
            '/api/auth/register',
            json={
                'email': 'duplicate@test.com',
                'password': 'Pass123!',
                'first_name': 'First',
                'last_name': 'User',
                'phone': '9876543212',
                'role': 'buyer'
            }
        )
        
        # Duplicate registration
        response = client.post(
            '/api/auth/register',
            json={
                'email': 'duplicate@test.com',
                'password': 'AnotherPass123!',
                'first_name': 'Second',
                'last_name': 'User',
                'phone': '9876543213',
                'role': 'buyer'
            }
        )
        
        assert response.status_code == 400
        data = response.json
        assert 'already exists' in data['error'].lower()
    
    def test_login_success(self, client):
        """Test successful login"""
        # Register user
        client.post(
            '/api/auth/register',
            json={
                'email': 'login@test.com',
                'password': 'LoginPass123!',
                'first_name': 'Login',
                'last_name': 'Test',
                'phone': '9876543214',
                'role': 'buyer'
            }
        )
        
        # Login
        response = client.post(
            '/api/auth/login',
            json={
                'email': 'login@test.com',
                'password': 'LoginPass123!'
            }
        )
        
        assert response.status_code == 200
        data = response.json
        assert 'access_token' in data['data']
        assert 'refresh_token' in data['data']
    
    def test_login_wrong_password(self, client):
        """Test login with wrong password"""
        # Register user
        client.post(
            '/api/auth/register',
            json={
                'email': 'wrongpass@test.com',
                'password': 'CorrectPass123!',
                'first_name': 'Wrong',
                'last_name': 'Pass',
                'phone': '9876543215',
                'role': 'buyer'
            }
        )
        
        # Try login with wrong password
        response = client.post(
            '/api/auth/login',
            json={
                'email': 'wrongpass@test.com',
                'password': 'WrongPass123!'
            }
        )
        
        assert response.status_code == 401
        data = response.json
        assert 'error' in data
    
    def test_get_profile(self, client, auth_headers):
        """Test get profile endpoint"""
        response = client.get(
            '/api/auth/profile',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json
        assert 'data' in data
        assert 'email' in data['data']
    
    def test_profile_without_auth(self, client):
        """Test accessing protected route without auth"""
        response = client.get('/api/auth/profile')
        assert response.status_code == 401

# ============================================================================
# FARMER ENDPOINTS
# ============================================================================

class TestFarmerEndpoints:
    """Test farmer-specific endpoints"""
    
    @pytest.fixture
    def farmer_headers(self, client):
        """Get farmer JWT headers"""
        response = client.post(
            '/api/auth/register',
            json={
                'email': 'testfarmer@test.com',
                'password': 'FarmerTest123!',
                'first_name': 'Test',
                'last_name': 'Farmer',
                'phone': '9988776655',
                'role': 'farmer'
            }
        )
        
        token = response.json['data']['access_token']
        return {'Authorization': f'Bearer {token}'}
    
    def test_farmer_dashboard(self, client, farmer_headers):
        """Test farmer dashboard endpoint"""
        response = client.get(
            '/api/farmer/dashboard',
            headers=farmer_headers
        )
        
        assert response.status_code == 200
        data = response.json
        assert 'data' in data
    
    def test_create_product(self, client, farmer_headers):
        """Test create product endpoint"""
        response = client.post(
            '/api/farmer/products',
            json={
                'name': 'Organic Tomatoes',
                'description': 'Fresh organic tomatoes from farm',
                'price': 50,
                'category': 'vegetables',
                'stock': 100,
                'unit': 'kg'
            },
            headers=farmer_headers
        )
        
        assert response.status_code == 201
        data = response.json
        assert 'data' in data
        assert data['data']['name'] == 'Organic Tomatoes'

# ============================================================================
# BUYER ENDPOINTS
# ============================================================================

class TestBuyerEndpoints:
    """Test buyer-specific endpoints"""
    
    @pytest.fixture
    def buyer_headers(self, client):
        """Get buyer JWT headers"""
        response = client.post(
            '/api/auth/register',
            json={
                'email': 'testbuyer@test.com',
                'password': 'BuyerTest123!',
                'first_name': 'Test',
                'last_name': 'Buyer',
                'phone': '9988776656',
                'role': 'buyer'
            }
        )
        
        token = response.json['data']['access_token']
        return {'Authorization': f'Bearer {token}'}
    
    def test_get_products(self, client, buyer_headers):
        """Test get products endpoint"""
        response = client.get(
            '/api/buyer/products?page=1&limit=10',
            headers=buyer_headers
        )
        
        assert response.status_code == 200
        data = response.json
        assert 'data' in data
        assert 'pagination' in data
    
    def test_search_products(self, client, buyer_headers):
        """Test search products endpoint"""
        response = client.get(
            '/api/buyer/products/search?query=tomato',
            headers=buyer_headers
        )
        
        assert response.status_code == 200
        data = response.json
        assert 'data' in data

# ============================================================================
# ERROR HANDLING
# ============================================================================

class TestErrorHandling:
    """Test error handling"""
    
    def test_invalid_json(self, client):
        """Test invalid JSON request"""
        response = client.post(
            '/api/auth/login',
            data='invalid json',
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_missing_required_fields(self, client):
        """Test missing required fields"""
        response = client.post(
            '/api/auth/register',
            json={
                'email': 'incomplete@test.com'
                # Missing other required fields
            }
        )
        
        assert response.status_code == 400
    
    def test_not_found(self, client):
        """Test 404 endpoint"""
        response = client.get('/api/nonexistent')
        assert response.status_code == 404

# ============================================================================
# TEST RUNNER
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
