"""
Buyer Shopping Cart Routes
Handles: Add to cart, Remove, Update quantity, View cart
Path: /api/cart
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

import sys
sys.path.append('..')
from models.models import Cart, Product

buyer_cart_bp = Blueprint('buyer_cart', __name__, url_prefix='/api/cart')

# ====================================================================
# 1. GET CART - View all items in cart
# ====================================================================
@buyer_cart_bp.route('/', methods=['GET'])
@jwt_required()
def get_cart():
    """
    Get all items in buyer's cart
    
    Response:
    {
        "success": true,
        "cart_items": [
            {
                "cart_id": 1,
                "product_id": 1,
                "product_name": "Organic Tomatoes",
                "farmer_id": 1,
                "farmer_name": "Ravi Kumar",
                "quantity": 2,
                "unit_price": 40,
                "total_price": 80,
                "image": "url"
            }
        ],
        "item_count": 3,
        "summary": {
            "subtotal": 240,
            "tax": 24,
            "delivery_fee": 50,
            "total": 314
        }
    }
    """
    try:
        buyer_id = get_jwt_identity()
        
        cart = Cart()
        cart_items = cart.get_cart_items(buyer_id)
        
        if not cart_items:
            return jsonify({
                'success': True,
                'cart_items': [],
                'item_count': 0,
                'summary': {
                    'subtotal': 0,
                    'tax': 0,
                    'delivery_fee': 0,
                    'total': 0
                }
            }), 200
        
        # Calculate totals
        subtotal = 0
        formatted_items = []
        
        for item in cart_items:
            item_total = item['quantity'] * item['price_at_addition']
            subtotal += item_total
            
            formatted_items.append({
                'cart_id': item['cart_id'],
                'product_id': item['product_id'],
                'product_name': item['product_name'],
                'farmer_id': item['farmer_id'],
                'farmer_name': item['farmer_name'],
                'quantity': item['quantity'],
                'unit_price': float(item['price_at_addition']),
                'total_price': float(item_total),
                'image': item.get('image', '')
            })
        
        # Calculate tax (5%) and delivery fee
        tax = subtotal * 0.05
        delivery_fee = 50 if subtotal > 0 else 0
        total = subtotal + tax + delivery_fee
        
        return jsonify({
            'success': True,
            'cart_items': formatted_items,
            'item_count': len(formatted_items),
            'summary': {
                'subtotal': float(subtotal),
                'tax': float(tax),
                'delivery_fee': float(delivery_fee),
                'total': float(total)
            }
        }), 200
        
    except Exception as e:
        print(f"Error in get_cart: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch cart'}), 500


# ====================================================================
# 2. ADD TO CART
# ====================================================================
@buyer_cart_bp.route('/add', methods=['POST'])
@jwt_required()
def add_to_cart():
    """
    Add product to cart
    
    Request:
    {
        "product_id": 1,
        "quantity": 2
    }
    
    Response:
    {
        "success": true,
        "message": "Product added to cart",
        "cart_item": {
            "cart_id": 1,
            "product_id": 1,
            "quantity": 2,
            "total_price": 80
        }
    }
    """
    try:
        buyer_id = get_jwt_identity()
        data = request.get_json()
        
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)
        
        # Validate inputs
        if not product_id or quantity < 1:
            return jsonify({'success': False, 'error': 'Invalid product or quantity'}), 400
        
        # Get product details
        product = Product()
        product_data = product.get_product_by_id(product_id)
        
        if not product_data:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        
        # Check quantity available
        if quantity > product_data['quantity']:
            return jsonify({
                'success': False,
                'error': f'Only {product_data["quantity"]} units available'
            }), 400
        
        # Add to cart
        cart = Cart()
        cart_id = cart.add_to_cart(
            buyer_id=buyer_id,
            product_id=product_id,
            farmer_id=product_data['farmer_id'],
            quantity=quantity,
            price=product_data['price']
        )
        
        if not cart_id:
            return jsonify({'success': False, 'error': 'Failed to add to cart'}), 500
        
        total_price = quantity * product_data['price']
        
        return jsonify({
            'success': True,
            'message': 'Product added to cart successfully',
            'cart_item': {
                'cart_id': cart_id,
                'product_id': product_id,
                'product_name': product_data['name'],
                'quantity': quantity,
                'unit_price': float(product_data['price']),
                'total_price': float(total_price)
            }
        }), 201
        
    except Exception as e:
        print(f"Error in add_to_cart: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to add to cart'}), 500


# ====================================================================
# 3. UPDATE CART ITEM - Update quantity
# ====================================================================
@buyer_cart_bp.route('/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_cart_item(product_id):
    """
    Update quantity of product in cart
    
    Request:
    {
        "quantity": 3
    }
    
    Response:
    {
        "success": true,
        "message": "Cart updated",
        "cart_item": {
            "product_id": 1,
            "quantity": 3,
            "total_price": 120
        }
    }
    """
    try:
        buyer_id = get_jwt_identity()
        data = request.get_json()
        quantity = data.get('quantity', 1)
        
        # Validate quantity
        if quantity < 1:
            return jsonify({'success': False, 'error': 'Quantity must be at least 1'}), 400
        
        # Check product availability
        product = Product()
        product_data = product.get_product_by_id(product_id)
        
        if not product_data:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        
        if quantity > product_data['quantity']:
            return jsonify({
                'success': False,
                'error': f'Only {product_data["quantity"]} units available'
            }), 400
        
        # Update cart
        cart = Cart()
        success = cart.update_cart_item(buyer_id, product_id, quantity)
        
        if not success:
            return jsonify({'success': False, 'error': 'Product not in cart'}), 404
        
        total_price = quantity * product_data['price']
        
        return jsonify({
            'success': True,
            'message': 'Cart updated successfully',
            'cart_item': {
                'product_id': product_id,
                'product_name': product_data['name'],
                'quantity': quantity,
                'unit_price': float(product_data['price']),
                'total_price': float(total_price)
            }
        }), 200
        
    except Exception as e:
        print(f"Error in update_cart_item: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to update cart'}), 500


# ====================================================================
# 4. REMOVE FROM CART
# ====================================================================
@buyer_cart_bp.route('/<int:product_id>', methods=['DELETE'])
@jwt_required()
def remove_from_cart(product_id):
    """
    Remove product from cart
    
    Response:
    {
        "success": true,
        "message": "Product removed from cart"
    }
    """
    try:
        buyer_id = get_jwt_identity()
        
        cart = Cart()
        success = cart.remove_from_cart(buyer_id, product_id)
        
        if not success:
            return jsonify({'success': False, 'error': 'Product not found in cart'}), 404
        
        return jsonify({
            'success': True,
            'message': 'Product removed from cart successfully'
        }), 200
        
    except Exception as e:
        print(f"Error in remove_from_cart: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to remove from cart'}), 500


# ====================================================================
# 5. CLEAR CART - Remove all items
# ====================================================================
@buyer_cart_bp.route('/', methods=['DELETE'])
@jwt_required()
def clear_cart():
    """
    Clear entire cart
    
    Response:
    {
        "success": true,
        "message": "Cart cleared successfully"
    }
    """
    try:
        buyer_id = get_jwt_identity()
        
        cart = Cart()
        success = cart.clear_cart(buyer_id)
        
        if not success:
            return jsonify({'success': False, 'error': 'Failed to clear cart'}), 500
        
        return jsonify({
            'success': True,
            'message': 'Cart cleared successfully'
        }), 200
        
    except Exception as e:
        print(f"Error in clear_cart: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to clear cart'}), 500


# ====================================================================
# 6. GET CART SUMMARY - Just totals without items
# ====================================================================
@buyer_cart_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_cart_summary():
    """
    Get cart totals and summary
    
    Response:
    {
        "success": true,
        "summary": {
            "item_count": 3,
            "subtotal": 240,
            "tax": 24,
            "delivery_fee": 50,
            "total": 314,
            "savings": 10
        }
    }
    """
    try:
        buyer_id = get_jwt_identity()
        
        cart = Cart()
        cart_items = cart.get_cart_items(buyer_id)
        
        if not cart_items:
            return jsonify({
                'success': True,
                'summary': {
                    'item_count': 0,
                    'subtotal': 0,
                    'tax': 0,
                    'delivery_fee': 0,
                    'total': 0,
                    'savings': 0
                }
            }), 200
        
        # Calculate totals
        subtotal = sum(item['quantity'] * item['price_at_addition'] for item in cart_items)
        tax = subtotal * 0.05
        delivery_fee = 50 if subtotal > 0 else 0
        total = subtotal + tax + delivery_fee
        
        # Calculate potential savings (e.g., from bulk discounts)
        savings = 0
        
        return jsonify({
            'success': True,
            'summary': {
                'item_count': len(cart_items),
                'subtotal': float(subtotal),
                'tax': float(tax),
                'delivery_fee': float(delivery_fee),
                'total': float(total),
                'savings': float(savings)
            }
        }), 200
        
    except Exception as e:
        print(f"Error in get_cart_summary: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch cart summary'}), 500


# ====================================================================
# 7. VALIDATE CART - Check all items are still available
# ====================================================================
@buyer_cart_bp.route('/validate', methods=['POST'])
@jwt_required()
def validate_cart():
    """
    Validate if all cart items are still available for checkout
    
    Response:
    {
        "success": true,
        "valid": true,
        "issues": []  // Empty if all valid
    }
    """
    try:
        buyer_id = get_jwt_identity()
        
        cart = Cart()
        cart_items = cart.get_cart_items(buyer_id)
        
        issues = []
        product = Product()
        
        for item in cart_items:
            product_data = product.get_product_by_id(item['product_id'])
            
            if not product_data:
                issues.append({
                    'product_id': item['product_id'],
                    'issue': 'Product no longer available'
                })
            elif item['quantity'] > product_data['quantity']:
                issues.append({
                    'product_id': item['product_id'],
                    'issue': f'Only {product_data["quantity"]} units available, {item["quantity"]} in cart'
                })
            elif product_data['price'] != item['price_at_addition']:
                issues.append({
                    'product_id': item['product_id'],
                    'issue': f'Price changed from {item["price_at_addition"]} to {product_data["price"]}'
                })
        
        return jsonify({
            'success': True,
            'valid': len(issues) == 0,
            'issues': issues
        }), 200
        
    except Exception as e:
        print(f"Error in validate_cart: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to validate cart'}), 500
