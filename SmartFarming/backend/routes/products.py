"""
Products Routes - Add, Edit, Delete, View Products
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.models import Product
import json

products_bp = Blueprint('products', __name__)

# ==================== GET ALL FARMER PRODUCTS ====================
@products_bp.route('/', methods=['GET'])
@jwt_required()
def get_products():
    """
    Get all products for logged-in farmer
    
    Query params: ?category=vegetables&sort=price
    
    Response: {
        "success": true,
        "products": [...]
    }
    """
    try:
        farmer_id = get_jwt_identity()
        category = request.args.get('category')
        sort = request.args.get('sort', 'created_at')
        
        # Get all products
        products = Product.get_farmer_products(farmer_id)
        
        # Filter by category if provided
        if category and products:
            products = [p for p in products if p['category'].lower() == category.lower()]
        
        # Format response
        formatted_products = [
            {
                'id': p['id'],
                'name': p['name'],
                'category': p['category'],
                'quantity': p['quantity'],
                'unit': p['unit'],
                'price': float(p['price']),
                'description': p['description'],
                'images': json.loads(p['images']) if p.get('images') else [],
                'average_rating': float(p.get('average_rating') or 0),
                'total_reviews': p.get('total_reviews', 0),
                'organic': bool(p.get('organic', False)),
                'status': p.get('status', 'approved'),
                'harvest_date': p['harvest_date'].isoformat() if p.get('harvest_date') else None,
                'is_available': p['is_available'],
                'created_at': p['created_at'].isoformat() if p.get('created_at') else None
            }
            for p in products
        ] if products else []
        
        return {
            'success': True,
            'total': len(formatted_products),
            'products': formatted_products
        }, 200
    
    except Exception as e:
        return {'success': False, 'message': str(e)}, 500

# ==================== GET SINGLE PRODUCT ====================
@products_bp.route('/<int:product_id>', methods=['GET'])
@jwt_required()
def get_product(product_id):
    """
    Get single product details
    """
    try:
        farmer_id = get_jwt_identity()
        product = Product.get_product_by_id(product_id)
        
        if not product:
            return {'success': False, 'message': 'Product not found'}, 404
        
        # Verify ownership
        if str(product['farmer_id']) != str(farmer_id):
            return {'success': False, 'message': 'Unauthorized'}, 403
        
        return {
            'success': True,
            'product': {
                'id': product['id'],
                'name': product['name'],
                'category': product['category'],
                'description': product['description'],
                'quantity': product['quantity'],
                'unit': product['unit'],
                'price': float(product['price']),
                'harvest_date': product['harvest_date'].isoformat() if product.get('harvest_date') else None,
                'images': json.loads(product['images']) if product.get('images') else [],
                'location': product.get('location'),
                'average_rating': float(product.get('average_rating') or 0),
                'total_reviews': product.get('total_reviews', 0),
                'organic': bool(product.get('organic', False)),
                'status': product.get('status', 'approved'),
                'is_available': product['is_available']
            }
        }, 200
    
    except Exception as e:
        return {'success': False, 'message': str(e)}, 500

# ==================== CREATE PRODUCT ====================
@products_bp.route('/', methods=['POST'])
@jwt_required()
def create_product():
    """
    Create new product listing
    
    Request: {
        "name": "Tomato",
        "category": "Vegetables",
        "description": "Fresh organic tomatoes",
        "quantity": 50,
        "unit": "kg",
        "price": 45.50,
        "harvest_date": "2026-06-01",
        "location": "Hyderabad",
        "images": ["url1", "url2", "url3"]
    }
    
    Response: {
        "success": true,
        "product_id": 1,
        "message": "Product created successfully"
    }
    """
    try:
        farmer_id = get_jwt_identity()
        data = request.get_json()
        
        # Validation
        required_fields = ['name', 'category', 'quantity', 'price']
        if not all(field in data for field in required_fields):
            return {'success': False, 'message': 'Missing required fields'}, 400
        
        # Create product
        product_id = Product.create_product(
            farmer_id=farmer_id,
            name=data['name'],
            description=data.get('description'),
            category=data['category'],
            quantity=data['quantity'],
            price=data['price'],
            unit=data.get('unit', 'kg'),
            harvest_date=data.get('harvest_date'),
            location=data.get('location'),
            images=data.get('images', [])
        )
        
        return {
            'success': True,
            'message': 'Product created successfully',
            'product_id': product_id
        }, 201
    
    except Exception as e:
        return {'success': False, 'message': str(e)}, 500

# ==================== UPDATE PRODUCT ====================
@products_bp.route('/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    """
    Update product details
    
    Request: {
        "name": "Premium Tomato",
        "price": 50.00,
        "quantity": 45
    }
    """
    try:
        farmer_id = get_jwt_identity()
        data = request.get_json()
        
        # Verify ownership
        product = Product.get_product_by_id(product_id)
        if not product or str(product['farmer_id']) != str(farmer_id):
            return {'success': False, 'message': 'Unauthorized'}, 403
        
        # Update product
        Product.update_product(product_id, **data)
        
        return {
            'success': True,
            'message': 'Product updated successfully'
        }, 200
    
    except Exception as e:
        return {'success': False, 'message': str(e)}, 500

# ==================== DELETE PRODUCT ====================
@products_bp.route('/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    """
    Delete/Archive product
    """
    try:
        farmer_id = get_jwt_identity()
        
        # Verify ownership
        product = Product.get_product_by_id(product_id)
        if not product or str(product['farmer_id']) != str(farmer_id):
            return {'success': False, 'message': 'Unauthorized'}, 403
        
        # Delete product
        Product.delete_product(product_id)
        
        return {
            'success': True,
            'message': 'Product deleted successfully'
        }, 200
    
    except Exception as e:
        return {'success': False, 'message': str(e)}, 500

# ==================== SEARCH PRODUCTS ====================
@products_bp.route('/search', methods=['GET'])
def search_products():
    """
    Search products (public endpoint - for buyers)
    
    Query: ?q=tomato&category=vegetables&location=hyderabad
    
    Response: {
        "success": true,
        "total": 15,
        "products": [...]
    }
    """
    try:
        search_query = request.args.get('q', '').strip()
        category = request.args.get('category', '').strip()
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        if search_query:
            products = Product.search_products(search_query, limit, offset)
            total = Product.count_search_results(search_query)
        elif category:
            products = Product.get_products_by_category(category, limit, offset)
            total = Product.count_by_category(category)
        else:
            products = Product.get_all_products(limit, offset)
            total = Product.count_products()
        
        formatted = [{
            'id': p['id'], 'name': p['name'], 'category': p.get('category'),
            'price': float(p['price']), 'quantity': p.get('quantity'),
            'unit': p.get('unit', 'kg'), 'description': p.get('description'),
            'farmer_name': p.get('farmer_name'), 'farmer_location': p.get('farmer_location'),
            'average_rating': float(p.get('average_rating') or 0),
            'organic': bool(p.get('organic', False)),
            'images': json.loads(p['images']) if p.get('images') else [],
        } for p in (products or [])]
        
        return {'success': True, 'total': total, 'products': formatted}, 200
    
    except Exception as e:
        return {'success': False, 'message': str(e)}, 500
