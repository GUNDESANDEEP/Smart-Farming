"""
Farmer Routes - Profile management, Dashboard
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.models import Farmer, Product, Order, Wallet
from datetime import datetime, timedelta

farmer_bp = Blueprint('farmer', __name__)

# ==================== GET FARMER PROFILE ====================
@farmer_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """
    Get farmer's profile information
    
    Response: {
        "success": true,
        "farmer": {
            "id": 1,
            "name": "Ravi Kumar",
            "phone": "9876543210",
            "email": "ravi@example.com",
            "location": "Hyderabad",
            "land_area": 2.5,
            "crops_grown": "Tomato, Carrot",
            "experience_years": 5,
            "aadhar_verified": true
        }
    }
    """
    try:
        farmer_id = get_jwt_identity()
        farmer = Farmer.get_by_id(farmer_id)
        
        if not farmer:
            return {'success': False, 'message': 'Farmer not found'}, 404
        
        return {
            'success': True,
            'farmer': {
                'id': farmer['id'],
                'first_name': farmer['first_name'],
                'last_name': farmer['last_name'],
                'phone': farmer['phone'],
                'email': farmer['email'],
                'location': farmer['location'],
                'land_area': farmer['land_area_hectares'],
                'crops_grown': farmer['crops_grown'],
                'experience_years': farmer['experience_years'],
                'aadhar_verified': farmer['aadhar_number'] is not None,
                'profile_image': farmer['profile_image'],
                'is_verified': farmer['is_verified'],
                'bank_account': '****' + (farmer['bank_account'][-4:] if farmer['bank_account'] else ''),
                'created_at': farmer['created_at'].isoformat()
            }
        }, 200
    
    except Exception as e:
        return {'success': False, 'message': str(e)}, 500

# ==================== UPDATE FARMER PROFILE ====================
@farmer_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """
    Update farmer's profile information
    
    Request: {
        "first_name": "Ravi",
        "location": "Bangalore",
        "land_area": 3.5,
        "crops_grown": "Tomato, Carrot, Lettuce",
        "experience_years": 10,
        "bank_account": "12345678901234",
        "bank_ifsc": "SBIN0001234",
        "bank_name": "State Bank of India"
    }
    """
    try:
        farmer_id = get_jwt_identity()
        data = request.get_json()
        
        # Update profile
        Farmer.update_farmer_profile(farmer_id, **data)
        
        # Get updated farmer
        farmer = Farmer.get_farmer_by_id(farmer_id)
        
        return {
            'success': True,
            'message': 'Profile updated successfully',
            'farmer': {
                'id': farmer['id'],
                'first_name': farmer['first_name'],
                'last_name': farmer['last_name'],
                'phone': farmer['phone'],
                'email': farmer['email'],
                'location': farmer['location'],
                'land_area': farmer['land_area_hectares'],
                'crops_grown': farmer['crops_grown'],
                'experience_years': farmer['experience_years'],
                'aadhar_verified': farmer['aadhar_number'] is not None,
                'profile_image': farmer['profile_image'],
                'is_verified': farmer['is_verified'],
                'bank_account': '****' + (farmer['bank_account'][-4:] if farmer['bank_account'] else ''),
                'bank_name': farmer.get('bank_name', ''),
                'upi_id': farmer.get('upi_id', ''),
                'created_at': farmer['created_at'].isoformat()
            }
        }, 200
    
    except Exception as e:
        return {'success': False, 'message': str(e)}, 500

# ==================== GET DASHBOARD ====================
@farmer_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    """
    Get dashboard statistics
    
    Response: {
        "success": true,
        "dashboard": {
            "total_products": 4,
            "total_earnings": 54230,
            "pending_orders": 2,
            "available_balance": 12450,
            "total_sold": 150,
            "rating": 4.5,
            "recent_orders": [...]
        }
    }
    """
    try:
        farmer_id = get_jwt_identity()
        
        # Get all products
        products = Product.get_farmer_products(farmer_id)
        
        # Get wallet info
        wallet = Wallet.get_wallet(farmer_id)
        
        # Get orders (last 5)
        orders = Order.get_farmer_orders(farmer_id)[:5]
        
        # Calculate stats
        total_sold = sum([p['total_sold'] for p in products]) if products else 0
        avg_rating = sum([p['rating'] for p in products if p['rating']]) / len([p for p in products if p['rating']]) if products else 0
        
        pending_orders = len([o for o in orders if o['status'] == 'pending'])
        
        return {
            'success': True,
            'dashboard': {
                'total_products': len(products) if products else 0,
                'total_earnings': float(wallet['total_earnings']) if wallet else 0,
                'available_balance': float(wallet['balance']) if wallet else 0,
                'pending_orders': pending_orders,
                'total_sold': total_sold,
                'average_rating': round(avg_rating, 1),
                'recent_orders': [
                    {
                        'id': o['id'],
                        'product_name': o['product_name'],
                        'quantity': o['quantity'],
                        'total_price': float(o['total_price']),
                        'status': o['status'],
                        'created_at': o['created_at'].isoformat()
                    }
                    for o in orders
                ] if orders else []
            }
        }, 200
    
    except Exception as e:
        return {'success': False, 'message': str(e)}, 500

# ==================== COMPLETE PROFILE ====================
@farmer_bp.route('/complete-profile', methods=['POST'])
@jwt_required()
def complete_profile():
    """
    Complete farmer profile after signup
    
    Request: {
        "land_area": 2.5,
        "crops_grown": "Tomato, Carrot",
        "experience_years": 5,
        "latitude": 17.3850,
        "longitude": 78.4867,
        "aadhar_number": "123456789012"
    }
    """
    try:
        farmer_id = get_jwt_identity()
        data = request.get_json()
        
        # Update profile
        update_data = {
            'land_area_hectares': data.get('land_area'),
            'crops_grown': data.get('crops_grown'),
            'experience_years': data.get('experience_years'),
            'latitude': data.get('latitude'),
            'longitude': data.get('longitude'),
            'aadhar_number': data.get('aadhar_number')
        }
        
        Farmer.update_farmer_profile(farmer_id, **update_data)
        
        return {
            'success': True,
            'message': 'Profile completed successfully'
        }, 200
    
    except Exception as e:
        return {'success': False, 'message': str(e)}, 500


# ==================== PRODUCTS CRUD ====================

@farmer_bp.route('/products', methods=['GET'])
@jwt_required()
def get_products():
    """Get farmer's products"""
    try:
        farmer_id = get_jwt_identity()
        products = Product.get_farmer_products(farmer_id)
        if not products:
            products = []
        return jsonify({'success': True, 'products': products}), 200
    except Exception as e:
        print(f"Get farmer products error: {e}")
        return jsonify({'success': True, 'products': []}), 200


@farmer_bp.route('/products', methods=['POST'])
@jwt_required()
def create_product():
    """Create a new product"""
    try:
        farmer_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        name = str(data.get('name', '')).strip()
        description = str(data.get('description', '')).strip()
        category = str(data.get('category', 'Others')).strip()
        unit = str(data.get('unit', 'kg')).strip()
        location = str(data.get('location', '')).strip()
        
        # Convert to proper types early
        try:
            price = float(data.get('price', 0))
            quantity = float(data.get('quantity', 0))
        except (ValueError, TypeError):
            return jsonify({'error': 'Price and quantity must be numbers'}), 400
        
        # Discount percent (0-90)
        try:
            discount_percent = int(data.get('discount_percent', 0))
            discount_percent = max(0, min(90, discount_percent))
        except (ValueError, TypeError):
            discount_percent = 0
        
        if not name:
            return jsonify({'error': 'Product name is required'}), 400
        if price <= 0:
            return jsonify({'error': 'Valid price is required'}), 400
        
        # Use BaseModel for PostgreSQL compatibility
        from models.models import BaseModel
        product_id = BaseModel.execute_insert(
            """INSERT INTO products (farmer_id, name, description, category, price, quantity, unit, location, discount_percentage, status, is_available, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending', TRUE, NOW())""",
            (int(farmer_id), name, description, category, price, quantity, unit, location, discount_percent)
        )
        
        return jsonify({
            'success': True,
            'message': 'Product created! Waiting for admin approval.',
            'product': {
                'id': product_id,
                'name': name,
                'description': description,
                'category': category,
                'price': price,
                'quantity': quantity,
                'unit': unit,
                'location': location,
                'discount_percent': discount_percent,
                'status': 'pending',
            }
        }), 201
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@farmer_bp.route('/products/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    """Update a product (owner only)"""
    try:
        farmer_id = get_jwt_identity()
        from models.models import BaseModel
        
        # Verify ownership
        product = BaseModel.execute_query(
            "SELECT * FROM products WHERE id = %s", (product_id,), fetch_one=True
        )
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        if str(product['farmer_id']) != str(farmer_id):
            return jsonify({'error': 'Unauthorized - you can only edit your own products'}), 403
        
        data = request.get_json()
        
        # Build dynamic update
        updates = []
        params = []
        for field in ['name', 'description', 'category', 'price', 'quantity', 'unit', 'location', 'discount_percent']:
            if field in data:
                updates.append(f"{field} = %s")
                params.append(data[field])
        
        if updates:
            params.append(product_id)
            query = f"UPDATE products SET {', '.join(updates)} WHERE id = %s"
            BaseModel.execute_query(query, tuple(params))
        
        return jsonify({'success': True, 'message': 'Product updated'}), 200
    except Exception as e:
        print(f"Update product error: {e}")
        return jsonify({'error': str(e)}), 500


@farmer_bp.route('/products/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    """Delete a product (owner only)"""
    try:
        farmer_id = get_jwt_identity()
        from models.models import BaseModel
        
        product = BaseModel.execute_query(
            "SELECT farmer_id FROM products WHERE id = %s", (product_id,), fetch_one=True
        )
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        if str(product['farmer_id']) != str(farmer_id):
            return jsonify({'error': 'Unauthorized'}), 403
        
        BaseModel.execute_query("DELETE FROM products WHERE id = %s AND farmer_id = %s", (product_id, farmer_id))
        
        return jsonify({'success': True, 'message': 'Product deleted'}), 200
    except Exception as e:
        print(f"Delete product error: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== ORDERS ====================

@farmer_bp.route('/orders', methods=['GET'])
@jwt_required()
def get_orders():
    """Get farmer's orders"""
    try:
        farmer_id = get_jwt_identity()
        orders = Order.get_farmer_orders(farmer_id)
        if not orders:
            orders = []
        
        order_list = []
        for o in orders:
            order_list.append({
                'id': o.get('id'),
                'product_name': o.get('product_name', 'Unknown'),
                'buyer_name': o.get('buyer_first_name', o.get('buyer_name', 'Unknown')),
                'buyer_last_name': o.get('buyer_last_name', ''),
                'buyer_phone': o.get('buyer_phone', ''),
                'buyer_email': o.get('buyer_email', ''),
                'buyer_address': o.get('buyer_address', ''),
                'buyer_city': o.get('buyer_city', ''),
                'buyer_state': o.get('buyer_state', ''),
                'buyer_pincode': o.get('buyer_pincode', ''),
                'quantity': o.get('quantity', 0),
                'total': float(o.get('total_price', 0)) if o.get('total_price') else 0,
                'total_price': float(o.get('total_price', 0)) if o.get('total_price') else 0,
                'status': o.get('status', 'pending'),
                'created_at': o['created_at'].isoformat() if hasattr(o.get('created_at', ''), 'isoformat') else str(o.get('created_at', '')),
            })
        
        return jsonify({'success': True, 'orders': order_list}), 200
    except Exception as e:
        print(f"Get farmer orders error: {e}")
        return jsonify({'success': True, 'orders': []}), 200


# ==================== EARNINGS ====================

@farmer_bp.route('/earnings', methods=['GET'])
@jwt_required()
def get_earnings():
    """Get farmer's earnings"""
    try:
        farmer_id = get_jwt_identity()
        from models.models import BaseModel
        
        total_row = BaseModel.execute_query(
            "SELECT COALESCE(SUM(total_amount), 0) as total FROM orders WHERE farmer_id = %s AND status = 'delivered'",
            (farmer_id,), fetch_one=True
        )
        month_row = BaseModel.execute_query(
            "SELECT COALESCE(SUM(total_amount), 0) as thisMonth FROM orders WHERE farmer_id = %s AND status = 'delivered' AND EXTRACT(MONTH FROM created_at) = EXTRACT(MONTH FROM NOW()) AND EXTRACT(YEAR FROM created_at) = EXTRACT(YEAR FROM NOW())",
            (farmer_id,), fetch_one=True
        )
        pending_row = BaseModel.execute_query(
            "SELECT COALESCE(SUM(total_amount), 0) as pending FROM orders WHERE farmer_id = %s AND status IN ('pending', 'confirmed')",
            (farmer_id,), fetch_one=True
        )
        
        return jsonify({
            'success': True,
            'total': float(total_row['total']) if total_row else 0,
            'thisMonth': float(month_row['thisMonth']) if month_row else 0,
            'pending': float(pending_row['pending']) if pending_row else 0,
            'rating': 4.5
        }), 200
    except Exception as e:
        print(f"Get earnings error: {e}")
        return jsonify({'success': True, 'total': 0, 'thisMonth': 0, 'pending': 0, 'rating': 0}), 200
