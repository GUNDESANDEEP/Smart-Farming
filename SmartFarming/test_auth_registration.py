#!/usr/bin/env python3
"""
Test Script: Verify All Authentication Endpoints Are Registered
Checks that all three authentication modules (Farmer, Admin, Buyer) are properly registered
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_app_initialization():
    """Test that Flask app initializes without errors"""
    print("=" * 80)
    print("TEST 1: Flask App Initialization")
    print("=" * 80)
    
    try:
        # We need to set up a minimal database config for testing
        os.environ['DB_HOST'] = 'localhost'
        os.environ['DB_USER'] = 'root'
        os.environ['DB_PASSWORD'] = ''
        os.environ['DB_NAME'] = 'smart_farming_db'
        os.environ['JWT_SECRET_KEY'] = 'test-secret-key-for-testing'
        
        # Try to import the app
        from backend.app import app
        print("✅ Flask app imported successfully")
        
        return app
    except Exception as e:
        print(f"❌ Error importing app: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_blueprint_registration(app):
    """Test that all blueprints are registered"""
    print("\n" + "=" * 80)
    print("TEST 2: Blueprint Registration")
    print("=" * 80)
    
    expected_endpoints = {
        'Farmer Auth': ['/api/auth/send-otp', '/api/auth/verify-otp', '/api/auth/register', '/api/auth/login', '/api/auth/logout'],
        'Admin Auth': ['/api/admin-auth/login', '/api/admin-auth/logout'],
        'Buyer Auth': ['/api/buyer-auth/send-otp', '/api/buyer-auth/verify-otp', '/api/buyer-auth/signup', '/api/buyer-auth/login'],
        'Admin Dashboard': ['/api/admin/dashboard', '/api/admin/dashboard/metrics'],
        'Admin Products': ['/api/admin/products/pending', '/api/admin/products/approve'],
        'Admin Users': ['/api/admin/users/farmers', '/api/admin/users/buyers'],
        'Admin Orders': ['/api/admin/orders/', '/api/admin/orders/status'],
        'Admin Analytics': ['/api/admin/analytics/dashboard', '/api/admin/analytics/sales'],
        'Admin Monitoring': ['/api/admin/ai-monitoring/', '/api/admin/ai-monitoring/logs'],
        'Admin Advanced Features': ['/api/admin/advanced-features/batch/approve-products'],
        'Buyer Cart': ['/api/cart/', '/api/cart/add'],
        'Buyer Products': ['/api/products/', '/api/products/search'],
        'Buyer Orders': ['/api/orders/', '/api/orders/place'],
        'Buyer Payments': ['/api/payments/', '/api/payments/cod'],
        'Buyer Profile': ['/api/buyer/', '/api/buyer/profile'],
        'Buyer Reviews': ['/api/reviews/', '/api/reviews/submit'],
    }
    
    # Get all registered routes
    routes = {}
    for rule in app.url_map.iter_rules():
        if not rule.rule.startswith('/static'):
            routes[rule.rule] = rule.endpoint
    
    print(f"\nTotal registered endpoints: {len(routes)}\n")
    
    # Check for each expected module
    all_passed = True
    for module_name, expected_paths in expected_endpoints.items():
        module_found = False
        found_endpoints = []
        
        for path in expected_paths:
            if path in routes:
                module_found = True
                found_endpoints.append(path)
        
        if found_endpoints:
            print(f"✅ {module_name}: {len(found_endpoints)} endpoints found")
            for ep in found_endpoints:
                print(f"   - {ep}")
        else:
            print(f"⚠️  {module_name}: Some endpoints not found")
            print(f"   Looking for: {expected_paths[0]}")
            all_passed = False
    
    return all_passed


def test_import_blueprints():
    """Test that all blueprint imports work"""
    print("\n" + "=" * 80)
    print("TEST 3: Direct Blueprint Imports")
    print("=" * 80)
    
    blueprints_to_test = [
        ('Farmer Auth', 'backend.routes.auth', 'auth_bp'),
        ('Admin Auth', 'backend.routes.admin_auth', 'admin_auth_bp'),
        ('Buyer Auth', 'backend.routes.buyer_auth', 'buyer_auth_bp'),
        ('Admin Dashboard', 'backend.routes.admin_dashboard', 'admin_dashboard_bp'),
        ('Admin Products', 'backend.routes.admin_products', 'admin_products_bp'),
        ('Admin Users', 'backend.routes.admin_users', 'admin_users_bp'),
        ('Admin Orders', 'backend.routes.admin_orders', 'admin_orders_bp'),
        ('Admin Analytics', 'backend.routes.admin_analytics', 'admin_analytics_bp'),
        ('Admin Monitoring', 'backend.routes.admin_monitoring', 'admin_monitoring_bp'),
        ('Admin Advanced Features', 'backend.routes.admin_advanced_features', 'admin_advanced_features_bp'),
        ('Buyer Cart', 'backend.routes.buyer_cart', 'buyer_cart_bp'),
        ('Buyer Products', 'backend.routes.buyer_products', 'buyer_products_bp'),
        ('Buyer Orders', 'backend.routes.buyer_orders', 'buyer_orders_bp'),
        ('Buyer Payments', 'backend.routes.buyer_payments', 'buyer_payments_bp'),
        ('Buyer Profile', 'backend.routes.buyer_profile', 'buyer_profile_bp'),
        ('Buyer Reviews', 'backend.routes.buyer_reviews', 'buyer_reviews_bp'),
    ]
    
    all_passed = True
    for name, module, blueprint_var in blueprints_to_test:
        try:
            mod = __import__(module, fromlist=[blueprint_var])
            blueprint = getattr(mod, blueprint_var)
            print(f"✅ {name}: {blueprint_var} imported successfully")
        except ImportError as e:
            print(f"❌ {name}: Failed to import - {str(e)}")
            all_passed = False
        except AttributeError as e:
            print(f"❌ {name}: Blueprint variable {blueprint_var} not found - {str(e)}")
            all_passed = False
        except Exception as e:
            print(f"❌ {name}: Unexpected error - {str(e)}")
            all_passed = False
    
    return all_passed


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 15 + "SMART FARMING - AUTHENTICATION VERIFICATION TEST" + " " * 15 + "║")
    print("╚" + "═" * 78 + "╝")
    
    # Test 1: Import blueprints directly
    test1_passed = test_import_blueprints()
    
    # Test 2: Initialize Flask app
    app = test_app_initialization()
    
    if app:
        # Test 3: Check registered blueprints
        test3_passed = test_blueprint_registration(app)
    else:
        test3_passed = False
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    if test1_passed and app and test3_passed:
        print("✅ All authentication modules are properly registered!")
        print("\nAuthentication endpoints available:")
        print("  - Farmer:      /api/auth/*")
        print("  - Admin:       /api/admin-auth/*, /api/admin/*")
        print("  - Buyer:       /api/buyer-auth/*, /api/buyer/*, /api/cart/*, /api/payments/*, /api/reviews/*, /api/orders/*")
        return 0
    else:
        print("❌ Some tests failed. Please review errors above.")
        if not test1_passed:
            print("   - Blueprint import test failed")
        if not app:
            print("   - Flask app initialization failed")
        if not test3_passed:
            print("   - Blueprint registration test failed")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
