"""
Buyer Profile & Dashboard Routes
Handles: Profile CRUD, Addresses, Dashboard with recommendations
Path: /api/buyer
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

import sys
sys.path.append('..')
from models.models import BuyerProfile, BuyerAddress, Order, Product

buyer_profile_bp = Blueprint('buyer_profile', __name__, url_prefix='/api/buyer')

# ====================================================================
# 1. GET PROFILE - Get buyer's profile
# ====================================================================
@buyer_profile_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """
    Get buyer profile information
    
    Response:
    {
        "success": true,
        "profile": {
            "buyer_id": 1,
            "first_name": "Ramesh",
            "last_name": "Sharma",
            "email": "ramesh@example.com",
            "phone": "9876543200",
            "location": "Hyderabad",
            "city": "Hyderabad",
            "state": "Telangana",
            "pincode": "500001",
            "total_orders": 15,
            "member_since": "2026-01-15"
        }
    }
    """
    try:
        buyer_id = get_jwt_identity()
        
        buyer = BuyerProfile()
        profile_data = buyer.get_buyer_by_id(buyer_id)
        
        if not profile_data:
            return jsonify({'success': False, 'error': 'Profile not found'}), 404
        
        # Get order count
        order_obj = Order()
        total_orders = order_obj.count_buyer_orders(buyer_id)
        
        return jsonify({
            'success': True,
            'profile': {
                'buyer_id': profile_data['buyer_id'],
                'first_name': profile_data['first_name'],
                'last_name': profile_data.get('last_name', ''),
                'email': profile_data['email'],
                'phone': profile_data['phone'],
                'location': profile_data.get('location', ''),
                'city': profile_data.get('city', ''),
                'state': profile_data.get('state', ''),
                'pincode': profile_data.get('pincode', ''),
                'total_orders': total_orders,
                'member_since': profile_data['created_at'].strftime('%Y-%m-%d') if profile_data['created_at'] else None
            }
        }), 200
        
    except Exception as e:
        print(f"Error in get_profile: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch profile'}), 500


# ====================================================================
# 2. UPDATE PROFILE - Update buyer information
# ====================================================================
@buyer_profile_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """
    Update buyer profile
    
    Request:
    {
        "first_name": "Ramesh",
        "last_name": "Kumar",
        "location": "Bangalore",
        "city": "Bangalore",
        "state": "Karnataka"
    }
    
    Response:
    {
        "success": true,
        "message": "Profile updated successfully"
    }
    """
    try:
        buyer_id = get_jwt_identity()
        data = request.get_json()
        
        # Extract fields to update
        update_fields = {}
        allowed_fields = ['first_name', 'last_name', 'phone', 'email', 'location', 'city', 'state', 'pincode']
        
        for field in allowed_fields:
            if field in data:
                update_fields[field] = data[field]
        
        if not update_fields:
            return jsonify({'success': False, 'error': 'No fields to update'}), 400
        
        # Update profile
        buyer = BuyerProfile()
        success = buyer.update_buyer(buyer_id, update_fields)
        
        if not success:
            return jsonify({'success': False, 'error': 'Failed to update profile'}), 500
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully'
        }), 200
        
    except Exception as e:
        print(f"Error in update_profile: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to update profile'}), 500


# ====================================================================
# 3. ADD DELIVERY ADDRESS
# ====================================================================
@buyer_profile_bp.route('/add-address', methods=['POST'])
@jwt_required()
def add_address():
    """
    Add new delivery address
    
    Request:
    {
        "type": "home",
        "address_line1": "123 Main Street",
        "address_line2": "Apt 4",
        "city": "Hyderabad",
        "state": "Telangana",
        "pincode": "500001",
        "latitude": 17.3850,
        "longitude": 78.4867,
        "is_default": false
    }
    
    Response:
    {
        "success": true,
        "address_id": 1,
        "message": "Address added successfully"
    }
    """
    try:
        buyer_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required = ['address_line1', 'city', 'state', 'pincode']
        if not all(field in data for field in required):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Create address
        address = BuyerAddress()
        address_id = address.create_address(
            buyer_id=buyer_id,
            type=data.get('type', 'other'),
            address_line1=data['address_line1'],
            address_line2=data.get('address_line2', ''),
            city=data['city'],
            state=data['state'],
            pincode=data['pincode'],
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            is_default=data.get('is_default', False)
        )
        
        if not address_id:
            return jsonify({'success': False, 'error': 'Failed to add address'}), 500
        
        return jsonify({
            'success': True,
            'address_id': address_id,
            'message': 'Address added successfully'
        }), 201
        
    except Exception as e:
        print(f"Error in add_address: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to add address'}), 500


# ====================================================================
# 4. GET ALL ADDRESSES
# ====================================================================
@buyer_profile_bp.route('/addresses', methods=['GET'])
@jwt_required()
def get_addresses():
    """
    Get all delivery addresses
    
    Response:
    {
        "success": true,
        "addresses": [
            {
                "address_id": 1,
                "type": "home",
                "address": "123 Main Street, Apt 4, Hyderabad, Telangana 500001",
                "city": "Hyderabad",
                "pincode": "500001",
                "is_default": true
            }
        ]
    }
    """
    try:
        buyer_id = get_jwt_identity()
        
        address = BuyerAddress()
        addresses = address.get_buyer_addresses(buyer_id)
        
        formatted_addresses = []
        for addr in addresses:
            formatted_addresses.append({
                'address_id': addr['address_id'],
                'type': addr['type'],
                'address': f"{addr['address_line1']}, {addr.get('address_line2', '')}, {addr['city']}, {addr['state']} {addr['pincode']}",
                'address_line1': addr['address_line1'],
                'address_line2': addr.get('address_line2', ''),
                'city': addr['city'],
                'state': addr['state'],
                'pincode': addr['pincode'],
                'latitude': float(addr['latitude']) if addr['latitude'] else None,
                'longitude': float(addr['longitude']) if addr['longitude'] else None,
                'is_default': addr['is_default']
            })
        
        return jsonify({
            'success': True,
            'addresses': formatted_addresses
        }), 200
        
    except Exception as e:
        print(f"Error in get_addresses: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch addresses'}), 500


# ====================================================================
# 5. UPDATE ADDRESS
# ====================================================================
@buyer_profile_bp.route('/address/<int:address_id>', methods=['PUT'])
@jwt_required()
def update_address(address_id):
    """
    Update delivery address
    
    Request:
    {
        "address_line1": "New Address",
        "city": "Bangalore"
    }
    
    Response:
    {
        "success": true,
        "message": "Address updated successfully"
    }
    """
    try:
        buyer_id = get_jwt_identity()
        data = request.get_json()
        
        # Verify address belongs to buyer
        address_obj = BuyerAddress()
        addr = address_obj.get_address_by_id(address_id, buyer_id)
        
        if not addr:
            return jsonify({'success': False, 'error': 'Address not found'}), 404
        
        # Update address
        success = address_obj.update_address(address_id, data)
        
        if not success:
            return jsonify({'success': False, 'error': 'Failed to update address'}), 500
        
        return jsonify({
            'success': True,
            'message': 'Address updated successfully'
        }), 200
        
    except Exception as e:
        print(f"Error in update_address: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to update address'}), 500


# ====================================================================
# 6. DELETE ADDRESS
# ====================================================================
@buyer_profile_bp.route('/address/<int:address_id>', methods=['DELETE'])
@jwt_required()
def delete_address(address_id):
    """
    Delete delivery address
    
    Response:
    {
        "success": true,
        "message": "Address deleted successfully"
    }
    """
    try:
        buyer_id = get_jwt_identity()
        
        # Verify address belongs to buyer
        address_obj = BuyerAddress()
        addr = address_obj.get_address_by_id(address_id, buyer_id)
        
        if not addr:
            return jsonify({'success': False, 'error': 'Address not found'}), 404
        
        # Delete address
        success = address_obj.delete_address(address_id)
        
        if not success:
            return jsonify({'success': False, 'error': 'Failed to delete address'}), 500
        
        return jsonify({
            'success': True,
            'message': 'Address deleted successfully'
        }), 200
        
    except Exception as e:
        print(f"Error in delete_address: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to delete address'}), 500


# ====================================================================
# 7. GET DASHBOARD - Home page with recommendations
# ====================================================================
@buyer_profile_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    """
    Get buyer dashboard with personalized recommendations
    
    Response:
    {
        "success": true,
        "dashboard": {
            "greeting": "Hello Ramesh!",
            "stats": {
                "total_orders": 15,
                "total_spent": 5000,
                "pending_orders": 2,
                "saved_addresses": 3
            },
            "personalized_recommendations": [
                {
                    "product_id": 1,
                    "name": "Organic Tomatoes",
                    "farmer_name": "Ravi Kumar",
                    "price": 40,
                    "rating": 4.5,
                    "reason": "Similar to your purchases"
                }
            ],
            "trending_products": [...],
            "order_status": {
                "pending": 2,
                "in_transit": 1,
                "delivered": 12
            }
        }
    }
    """
    try:
        buyer_id = get_jwt_identity()
        
        # Get buyer info
        buyer = BuyerProfile()
        buyer_data = buyer.get_buyer_by_id(buyer_id)
        
        # Get stats
        order_obj = Order()
        total_orders = order_obj.count_buyer_orders(buyer_id)
        total_spent = order_obj.get_buyer_total_spent(buyer_id)
        pending_orders = order_obj.count_by_status(buyer_id, 'pending')
        
        # Get address count
        address_obj = BuyerAddress()
        saved_addresses = address_obj.count_addresses(buyer_id)
        
        # Get trending products
        product_obj = Product()
        trending = product_obj.get_trending_products(limit=5)
        
        # Get personalized recommendations (based on purchase history)
        recommendations = product_obj.get_personalized_recommendations(buyer_id, limit=5)
        
        # Format trending products
        formatted_trending = []
        for p in trending[:5]:
            formatted_trending.append({
                'product_id': p['product_id'],
                'name': p['name'],
                'farmer_name': p['farmer_name'],
                'price': float(p['price']),
                'rating': p['rating'],
                'image': p['images'][0] if p['images'] else ''
            })
        
        # Format recommendations
        formatted_recommendations = []
        for p in recommendations[:5]:
            formatted_recommendations.append({
                'product_id': p['product_id'],
                'name': p['name'],
                'farmer_name': p['farmer_name'],
                'price': float(p['price']),
                'rating': p['rating'],
                'reason': p.get('reason', 'Recommended for you'),
                'image': p['images'][0] if p['images'] else ''
            })
        
        # Get order status breakdown
        status_breakdown = {
            'pending': order_obj.count_by_status(buyer_id, 'pending'),
            'in_transit': order_obj.count_by_status(buyer_id, 'in_transit'),
            'delivered': order_obj.count_by_status(buyer_id, 'delivered'),
            'cancelled': order_obj.count_by_status(buyer_id, 'cancelled')
        }
        
        return jsonify({
            'success': True,
            'dashboard': {
                'greeting': f"Hello {buyer_data['first_name']}!",
                'stats': {
                    'total_orders': total_orders,
                    'total_spent': float(total_spent) if total_spent else 0,
                    'pending_orders': pending_orders,
                    'saved_addresses': saved_addresses
                },
                'personalized_recommendations': formatted_recommendations,
                'trending_products': formatted_trending,
                'order_status': status_breakdown
            }
        }), 200
        
    except Exception as e:
        print(f"Error in get_dashboard: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch dashboard'}), 500


# ====================================================================
# 8. GET NOTIFICATION PREFERENCES
# ====================================================================
@buyer_profile_bp.route('/notification-preferences', methods=['GET'])
@jwt_required()
def get_notification_preferences():
    """
    Get notification preferences
    
    Response:
    {
        "success": true,
        "preferences": {
            "order_updates": true,
            "product_recommendations": true,
            "promotional": false,
            "flash_deals": true,
            "payment_reminders": true
        }
    }
    """
    try:
        buyer_id = get_jwt_identity()
        
        buyer = BuyerProfile()
        prefs = buyer.get_notification_preferences(buyer_id)
        
        if not prefs:
            # Default preferences
            prefs = {
                'order_updates': True,
                'product_recommendations': True,
                'promotional': False,
                'flash_deals': True,
                'payment_reminders': True
            }
        
        return jsonify({
            'success': True,
            'preferences': prefs
        }), 200
        
    except Exception as e:
        print(f"Error in get_notification_preferences: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch preferences'}), 500


# ====================================================================
# 9. UPDATE NOTIFICATION PREFERENCES
# ====================================================================
@buyer_profile_bp.route('/notification-preferences', methods=['PUT'])
@jwt_required()
def update_notification_preferences():
    """
    Update notification preferences
    
    Request:
    {
        "promotional": true,
        "flash_deals": false
    }
    
    Response:
    {
        "success": true,
        "message": "Preferences updated successfully"
    }
    """
    try:
        buyer_id = get_jwt_identity()
        data = request.get_json()
        
        buyer = BuyerProfile()
        success = buyer.update_notification_preferences(buyer_id, data)
        
        if not success:
            return jsonify({'success': False, 'error': 'Failed to update preferences'}), 500
        
        return jsonify({
            'success': True,
            'message': 'Preferences updated successfully'
        }), 200
        
    except Exception as e:
        print(f"Error in update_notification_preferences: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to update preferences'}), 500
