"""
Farmer Module - Complete Product and Order Management
"""

from fastapi import APIRouter, Request, Query, Depends
from fastapi.responses import JSONResponse
from utils.jwt_utils import get_current_user
from models.models import (
    User, Farmer, Product, Order, Review, Notification, Wallet,
    Transaction, BaseModel
)
from datetime import datetime
try:
    from slugify import slugify
except ImportError:
    def slugify(text):
        import re
        return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
import json
import uuid

farmer_router = APIRouter(prefix='/api/farmer', tags=['Farmer'])

# ============================================================================
# MIDDLEWARE - Verify User is Farmer
# ============================================================================

async def farmer_required(f, request: Request, user_id: str = Depends(get_current_user)):
    """Decorator to ensure user is a farmer"""
    def decorated_function(*args, **kwargs):
        # user_id from dependency injection
        farmer = BaseModel.execute_query("SELECT * FROM farmers WHERE id = %s", (int(user_id),), fetch_one=True)
        if not farmer:
            return JSONResponse(status_code=403, content={'error': 'Farmer access required'})
        
        kwargs['farmer'] = farmer
        return f(*args, **kwargs)
    
    decorated_function.__name__ = f.__name__
    return decorated_function

# ============================================================================
# DASHBOARD
# ============================================================================

@farmer_router.get('/dashboard')
async def dashboard(request: Request, user_id: str = Depends(get_current_user)):
    """Get farmer dashboard statistics"""
    try:
        # user_id from dependency injection
        farmer = BaseModel.execute_query("SELECT * FROM farmers WHERE id = %s", (int(user_id),), fetch_one=True)
        if not farmer:
            return JSONResponse(status_code=403, content={'error': 'Farmer access required'})
        
        farmer_id = farmer['id']
        
        # Product stats
        prod_stats = BaseModel.execute_query(
            "SELECT COUNT(*) as total_products FROM products WHERE farmer_id = %s", 
            (farmer_id,), fetch_one=True
        ) or {'total_products': 0}
        
        # Order stats
        order_stats = BaseModel.execute_query(
            """SELECT COUNT(*) as total_orders, 
                      SUM(CASE WHEN status='delivered' THEN 1 ELSE 0 END) as delivered_orders,
                      COALESCE(SUM(CASE WHEN status='delivered' THEN total_amount ELSE 0 END), 0) as total_earnings
               FROM orders WHERE farmer_id = %s""",
            (farmer_id,), fetch_one=True
        ) or {'total_orders': 0, 'delivered_orders': 0, 'total_earnings': 0}
        
        # Rating stats
        rating_stats = BaseModel.execute_query(
            """SELECT COALESCE(AVG(product_rating), 0) as average_rating, COUNT(*) as total_ratings 
               FROM buyer_reviews WHERE farmer_id = %s""",
            (farmer_id,), fetch_one=True
        ) or {'average_rating': 0, 'total_ratings': 0}
        
        # Recent products
        recent_products = BaseModel.execute_query(
            "SELECT id, name, price, quantity, unit, category, is_available FROM products WHERE farmer_id = %s ORDER BY created_at DESC LIMIT 5",
            (farmer_id,), fetch_all=True
        ) or []
        
        return JSONResponse(content={
            'success': True,
            'farmer_id': farmer_id,
            'name': f"{farmer.get('first_name', '')} {farmer.get('last_name', '')}".strip(),
            'location': farmer.get('location', ''),
            'stats': {
                'total_products': prod_stats.get('total_products', 0) or 0,
                'total_orders': order_stats.get('total_orders', 0) or 0,
                'delivered_orders': order_stats.get('delivered_orders', 0) or 0,
                'total_earnings': float(order_stats.get('total_earnings', 0) or 0),
                'average_rating': round(float(rating_stats.get('average_rating', 0) or 0), 1),
                'total_ratings': rating_stats.get('total_ratings', 0) or 0
            },
            'recent_products': recent_products
        }), 200
    
    except Exception as e:
        print(f"Dashboard error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})

# ============================================================================
# PRODUCT MANAGEMENT
# ============================================================================

@farmer_router.post('/products')
async def create_product(request: Request, user_id: str = Depends(get_current_user)):
    """Create new product"""
    try:
        # user_id from dependency injection
        farmer = BaseModel.execute_query("SELECT * FROM farmers WHERE id = %s", (int(user_id),), fetch_one=True)
        if not farmer:
            return JSONResponse(status_code=403, content={'error': 'Farmer access required'})
        
        data = await request.json()
        if not data:
            return JSONResponse(status_code=400, content={'error': 'No data provided'})
        
        # Validation
        name = str(data.get('name', '')).strip()
        category = str(data.get('category', 'Others')).strip()
        unit = str(data.get('unit', 'kg')).strip()
        description = str(data.get('description', '')).strip()
        location = str(data.get('location', '')).strip()
        
        # Convert to numbers FIRST
        try:
            price = float(data.get('price', 0))
            quantity = float(data.get('quantity', 0))
        except (ValueError, TypeError):
            return JSONResponse(status_code=400, content={'error': 'Price and quantity must be numbers'})
        
        if not name:
            return JSONResponse(status_code=400, content={'error': 'Product name is required'})
        if price <= 0:
            return JSONResponse(status_code=400, content={'error': 'Price must be positive'})
        if quantity <= 0:
            return JSONResponse(status_code=400, content={'error': 'Quantity must be positive'})
        
        images = json.dumps(data.get('images', []) if data.get('images') else [])
        is_organic = data.get('is_organic', False)
        harvest_date = data.get('harvest_date')
        discount_percentage = float(data.get('discount_percentage', 0))
        
        product_id = BaseModel.execute_insert(
            """INSERT INTO products (farmer_id, name, category, description, price, quantity, unit, 
                                     images, is_organic, harvest_date, location, discount_percentage, is_available, status)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE, 'pending')""",
            (farmer['id'], name, category, description, price, quantity, unit,
             images, is_organic, harvest_date, location, discount_percentage)
        )
        
        return JSONResponse(status_code=201, content={
            'success': True,
            'message': 'Product created! Waiting for admin approval.',
            'product': {
                'id': product_id,
                'name': name,
                'category': category,
                'description': description,
                'price': price,
                'quantity': quantity,
                'unit': unit,
                'location': location,
                'status': 'pending',
            }
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={'error': str(e)})

@farmer_router.get('/products')
async def get_products(request: Request, user_id: str = Depends(get_current_user)):
    """Get farmer's products"""
    try:
        # user_id from dependency injection
        farmer = BaseModel.execute_query("SELECT * FROM farmers WHERE id = %s", (int(user_id),), fetch_one=True)
        if not farmer:
            return JSONResponse(status_code=403, content={'error': 'Farmer access required'})
        if not farmer:
            return JSONResponse(status_code=404, content={'error': 'Farmer profile not found'})
        
        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 20))
        offset = (page - 1) * limit
        
        products = Product.get_by_farmer(farmer['id'], limit=limit, offset=offset)
        
        return {
            'products': products,
            'page': page,
            'limit': limit
        }
    
    except Exception as e:
        print(f"Get products error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})

@farmer_router.get('/products/{product_id}')
async def get_product(product_id: int, request: Request, user_id: str = Depends(get_current_user)):
    """Get product details"""
    try:
        # user_id from dependency injection
        farmer = BaseModel.execute_query("SELECT * FROM farmers WHERE id = %s", (int(user_id),), fetch_one=True)
        if not farmer:
            return JSONResponse(status_code=403, content={'error': 'Farmer access required'})
        
        product = Product.get_by_id(product_id)
        if not product:
            return JSONResponse(status_code=404, content={'error': 'Product not found'})
        
        # Verify product belongs to farmer
        if product['farmer_id'] != farmer['id']:
            return JSONResponse(status_code=403, content={'error': 'Unauthorized'})
        
        return {'product': product}
    
    except Exception as e:
        print(f"Get product error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})

@farmer_router.put('/products/{product_id}')
async def update_product(product_id: int, request: Request, user_id: str = Depends(get_current_user)):
    """Update product"""
    try:
        # user_id from dependency injection
        farmer = BaseModel.execute_query("SELECT * FROM farmers WHERE id = %s", (int(user_id),), fetch_one=True)
        if not farmer:
            return JSONResponse(status_code=403, content={'error': 'Farmer access required'})
        
        product = Product.get_by_id(product_id)
        if not product:
            return JSONResponse(status_code=404, content={'error': 'Product not found'})
        
        if product['farmer_id'] != farmer['id']:
            return JSONResponse(status_code=403, content={'error': 'Unauthorized'})
        
        data = await request.json()
        update_fields = {}
        
        allowed_fields = ['name', 'description', 'detailed_description', 'quantity',
                         'price', 'min_order_quantity', 'max_order_quantity',
                         'discount_percentage', 'harvest_date', 'expiry_date',
                         'images', 'specifications', 'certifications', 'is_organic',
                         'is_available', 'location', 'category', 'unit']
        
        for field in allowed_fields:
            if field in data:
                if field in ['images', 'specifications', 'certifications']:
                    update_fields[field] = json.dumps(data[field])
                else:
                    update_fields[field] = data[field]
        
        Product.update(product_id, **update_fields)
        
        # Auto-restore sold-out products when farmer restocks
        if 'quantity' in update_fields:
            new_qty = float(update_fields['quantity'])
            if new_qty > 0 and product.get('status') == 'sold_out':
                BaseModel.execute_query(
                    "UPDATE products SET status = 'approved', is_available = true WHERE id = %s",
                    (product_id,)
                )
        
        return {'message': 'Product updated successfully'}
    
    except Exception as e:
        print(f"Update product error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})

@farmer_router.delete('/products/{product_id}')
async def delete_product(product_id: int, request: Request, user_id: str = Depends(get_current_user)):
    """Delete product"""
    try:
        # user_id from dependency injection
        farmer = BaseModel.execute_query("SELECT * FROM farmers WHERE id = %s", (int(user_id),), fetch_one=True)
        if not farmer:
            return JSONResponse(status_code=403, content={'error': 'Farmer access required'})
        
        product = Product.get_by_id(product_id)
        if not product:
            return JSONResponse(status_code=404, content={'error': 'Product not found'})
        
        if product['farmer_id'] != farmer['id']:
            return JSONResponse(status_code=403, content={'error': 'Unauthorized'})
        
        Product.update(product_id, is_available=False)
        
        return {'message': 'Product deleted successfully'}
    
    except Exception as e:
        print(f"Delete product error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})

# ============================================================================
# ORDER MANAGEMENT
# ============================================================================

@farmer_router.get('/orders')
async def get_orders(request: Request, user_id: str = Depends(get_current_user)):
    """Get farmer's orders"""
    try:
        # user_id from dependency injection
        farmer = BaseModel.execute_query("SELECT * FROM farmers WHERE id = %s", (int(user_id),), fetch_one=True)
        if not farmer:
            return JSONResponse(status_code=403, content={'error': 'Farmer access required'})
        if not farmer:
            return JSONResponse(status_code=404, content={'error': 'Farmer profile not found'})
        
        status = request.query_params.get('status')
        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 20))
        offset = (page - 1) * limit
        
        orders = Order.get_farmer_orders(farmer['id'], status=status, limit=limit, offset=offset)
        
        return {
            'orders': orders,
            'page': page,
            'limit': limit
        }
    
    except Exception as e:
        print(f"Get orders error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})

@farmer_router.get('/orders/{order_id}')
async def get_order(order_id: int, request: Request, user_id: str = Depends(get_current_user)):
    """Get order details"""
    try:
        # user_id from dependency injection
        farmer = BaseModel.execute_query("SELECT * FROM farmers WHERE id = %s", (int(user_id),), fetch_one=True)
        if not farmer:
            return JSONResponse(status_code=403, content={'error': 'Farmer access required'})
        
        order = Order.get_by_id(order_id)
        if not order:
            return JSONResponse(status_code=404, content={'error': 'Order not found'})
        
        if order['farmer_id'] != farmer['id']:
            return JSONResponse(status_code=403, content={'error': 'Unauthorized'})
        
        return {'order': order}
    
    except Exception as e:
        print(f"Get order error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})

@farmer_router.put('/orders/{order_id}/status')
async def update_order_status(order_id: int, request: Request, user_id: str = Depends(get_current_user)):
    """Update order status"""
    try:
        # user_id from dependency injection
        farmer = BaseModel.execute_query("SELECT * FROM farmers WHERE id = %s", (int(user_id),), fetch_one=True)
        if not farmer:
            return JSONResponse(status_code=403, content={'error': 'Farmer access required'})
        
        order = Order.get_by_id(order_id)
        if not order:
            return JSONResponse(status_code=404, content={'error': 'Order not found'})
        
        if order['farmer_id'] != farmer['id']:
            return JSONResponse(status_code=403, content={'error': 'Unauthorized'})
        
        data = await request.json()
        new_status = data.get('status')
        
        valid_statuses = ['confirmed', 'processing', 'shipped', 'delivered', 'cancelled', 'rejected']
        if new_status not in valid_statuses:
            return JSONResponse(content={'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
        
        Order.update_status(order_id, new_status)
        
        # Send notification to buyer
        Notification.create(
            user_id=order['buyer_user_id'],
            title='Order Status Updated',
            message=f'Your order #{order["order_number"]} status has been updated to {new_status}',
            notification_type='order'
        )
        
        return {'message': 'Order status updated successfully'}
    
    except Exception as e:
        print(f"Update order status error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})

@farmer_router.post('/orders/{order_id}/accept')
async def accept_order(order_id: int, request: Request, user_id: str = Depends(get_current_user)):
    """Accept order"""
    try:
        # user_id from dependency injection
        farmer = BaseModel.execute_query("SELECT * FROM farmers WHERE id = %s", (int(user_id),), fetch_one=True)
        if not farmer:
            return JSONResponse(status_code=403, content={'error': 'Farmer access required'})
        
        order = Order.get_by_id(order_id)
        if not order:
            return JSONResponse(status_code=404, content={'error': 'Order not found'})
        
        if order['farmer_id'] != farmer['id']:
            return JSONResponse(status_code=403, content={'error': 'Unauthorized'})
        
        if order['status'] != 'pending':
            return JSONResponse(status_code=400, content={'error': 'Can only accept pending orders'})
        
        Order.update_status(order_id, 'confirmed')
        
        # Send notification
        Notification.create(
            user_id=order['buyer_user_id'],
            title='Order Accepted',
            message=f'Your order #{order["order_number"]} has been accepted',
            notification_type='order'
        )
        
        return {'message': 'Order accepted successfully'}
    
    except Exception as e:
        print(f"Accept order error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})

@farmer_router.post('/orders/{order_id}/reject')
async def reject_order(order_id: int, request: Request, user_id: str = Depends(get_current_user)):
    """Reject order"""
    try:
        # user_id from dependency injection
        farmer = BaseModel.execute_query("SELECT * FROM farmers WHERE id = %s", (int(user_id),), fetch_one=True)
        if not farmer:
            return JSONResponse(status_code=403, content={'error': 'Farmer access required'})
        
        order = Order.get_by_id(order_id)
        if not order:
            return JSONResponse(status_code=404, content={'error': 'Order not found'})
        
        if order['farmer_id'] != farmer['id']:
            return JSONResponse(status_code=403, content={'error': 'Unauthorized'})
        
        if order['status'] != 'pending':
            return JSONResponse(status_code=400, content={'error': 'Can only reject pending orders'})
        
        data = await request.json()
        reason = data.get('reason', 'No reason provided')
        
        Order.update_status(order_id, 'rejected')
        BaseModel.execute_query(
            "UPDATE orders SET rejection_reason = %s WHERE id = %s",
            (reason, order_id)
        )
        
        # Send notification
        Notification.create(
            user_id=order['buyer_user_id'],
            title='Order Rejected',
            message=f'Your order #{order["order_number"]} has been rejected. Reason: {reason}',
            notification_type='order'
        )
        
        return {'message': 'Order rejected successfully'}
    
    except Exception as e:
        print(f"Reject order error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})

# ============================================================================
# EARNINGS & WALLET
# ============================================================================

@farmer_router.get('/earnings')
async def get_earnings(request: Request, user_id: str = Depends(get_current_user)):
    """Get farmer earnings from orders + receipts"""
    try:
        # user_id from dependency injection
        farmer = BaseModel.execute_query("SELECT * FROM farmers WHERE id = %s", (int(user_id),), fetch_one=True)
        if not farmer:
            return JSONResponse(status_code=403, content={'error': 'Farmer access required'})
        
        farmer_id = farmer['id']
        
        # Total from receipts (direct sales + online)
        receipt_earnings = BaseModel.execute_query(
            """SELECT 
                COALESCE(SUM(grand_total), 0) as total,
                COALESCE(SUM(CASE WHEN EXTRACT(MONTH FROM created_at) = EXTRACT(MONTH FROM NOW()) AND EXTRACT(YEAR FROM created_at) = EXTRACT(YEAR FROM NOW()) THEN grand_total ELSE 0 END), 0) as this_month,
                COALESCE(SUM(CASE WHEN DATE(created_at) = CURRENT_DATE THEN grand_total ELSE 0 END), 0) as today,
                COUNT(*) as total_sales
               FROM receipts WHERE farmer_id = %s AND payment_status = 'completed'""",
            (farmer_id,), fetch_one=True
        ) or {'total': 0, 'this_month': 0, 'today': 0, 'total_sales': 0}
        
        # Also try orders table for backward compatibility
        order_earnings = BaseModel.execute_query(
            "SELECT COALESCE(SUM(total_amount), 0) as total FROM orders WHERE farmer_id = %s AND status = 'delivered'",
            (farmer_id,), fetch_one=True
        ) or {'total': 0}
        
        # Recent sales (last 10)
        recent_sales = BaseModel.execute_query(
            """SELECT receipt_id, buyer_name, grand_total, payment_type, created_at 
               FROM receipts WHERE farmer_id = %s ORDER BY created_at DESC LIMIT 10""",
            (farmer_id,), fetch_all=True
        ) or []
        
        # Serialize dates and decimals
        for sale in recent_sales:
            if sale.get('created_at'):
                sale['created_at'] = sale['created_at'].isoformat() if hasattr(sale['created_at'], 'isoformat') else str(sale['created_at'])
            if sale.get('grand_total') is not None:
                sale['grand_total'] = float(sale['grand_total'])
        
        total = float(receipt_earnings['total']) + float(order_earnings['total'])
        
        return {
            'success': True,
            'total': total,
            'total_earnings': total,
            'thisMonth': float(receipt_earnings['this_month']),
            'today': float(receipt_earnings['today']),
            'total_sales': int(receipt_earnings['total_sales']),
            'pending': 0,
            'recent_sales': recent_sales,
        }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={'error': str(e)})

@farmer_router.get('/transactions')
async def get_transactions(request: Request, user_id: str = Depends(get_current_user)):
    """Get transaction history"""
    try:
        # user_id from dependency injection
        farmer = BaseModel.execute_query("SELECT * FROM farmers WHERE id = %s", (int(user_id),), fetch_one=True)
        if not farmer:
            return JSONResponse(status_code=403, content={'error': 'Farmer access required'})
        
        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 20))
        offset = (page - 1) * limit
        
        query = """
        SELECT * FROM transactions
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """
        
        transactions = BaseModel.execute_query(query, (user_id, limit, offset), fetch_all=True)
        
        return {
            'transactions': transactions,
            'page': page,
            'limit': limit
        }
    
    except Exception as e:
        print(f"Get transactions error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})

# ============================================================================
# REVIEWS & RATINGS
# ============================================================================

@farmer_router.get('/reviews')
async def get_reviews(request: Request, user_id: str = Depends(get_current_user)):
    """Get reviews for farmer's products"""
    try:
        # user_id from dependency injection
        farmer = BaseModel.execute_query("SELECT * FROM farmers WHERE id = %s", (int(user_id),), fetch_one=True)
        if not farmer:
            return JSONResponse(status_code=403, content={'error': 'Farmer access required'})
        
        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 20))
        offset = (page - 1) * limit
        
        query = """
        SELECT r.*, p.name as product_name, u.first_name, u.last_name
        FROM reviews r
        LEFT JOIN products p ON r.product_id = p.id
        LEFT JOIN buyers b ON r.buyer_id = b.id
        LEFT JOIN users u ON b.user_id = u.id
        WHERE p.farmer_id = %s
        ORDER BY r.created_at DESC
        LIMIT %s OFFSET %s
        """
        
        reviews = BaseModel.execute_query(query, (farmer['id'], limit, offset), fetch_all=True)
        
        return {
            'reviews': reviews,
            'page': page,
            'limit': limit
        }
    
    except Exception as e:
        print(f"Get reviews error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})

@farmer_router.get('/ratings')
async def get_ratings(request: Request, user_id: str = Depends(get_current_user)):
    """Get farmer ratings"""
    try:
        # user_id from dependency injection
        farmer = BaseModel.execute_query("SELECT * FROM farmers WHERE id = %s", (int(user_id),), fetch_one=True)
        if not farmer:
            return JSONResponse(status_code=403, content={'error': 'Farmer access required'})
        
        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 20))
        offset = (page - 1) * limit
        
        query = """
        SELECT fr.*, u.first_name, u.last_name
        FROM farmer_ratings fr
        LEFT JOIN buyers b ON fr.buyer_id = b.id
        LEFT JOIN users u ON b.user_id = u.id
        WHERE fr.farmer_id = %s
        ORDER BY fr.created_at DESC
        LIMIT %s OFFSET %s
        """
        
        ratings = BaseModel.execute_query(query, (farmer['id'], limit, offset), fetch_all=True)
        
        return {
            'ratings': ratings,
            'page': page,
            'limit': limit
        }
    
    except Exception as e:
        print(f"Get ratings error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})

# ============================================================================
# PROFILE MANAGEMENT
# ============================================================================

@farmer_router.get('/profile')
async def get_farmer_profile(request: Request, user_id: str = Depends(get_current_user)):
    """Get farmer profile"""
    try:
        # user_id from dependency injection
        farmer = BaseModel.execute_query("SELECT * FROM farmers WHERE id = %s", (int(user_id),), fetch_one=True)
        if not farmer:
            return JSONResponse(status_code=403, content={'error': 'Farmer access required'})
        
        return {'profile': farmer}
    
    except Exception as e:
        print(f"Get profile error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})

@farmer_router.put('/profile')
async def update_farmer_profile(request: Request, user_id: str = Depends(get_current_user)):
    """Update farmer profile"""
    try:
        # user_id from dependency injection
        farmer = BaseModel.execute_query("SELECT * FROM farmers WHERE id = %s", (int(user_id),), fetch_one=True)
        if not farmer:
            return JSONResponse(status_code=403, content={'error': 'Farmer access required'})
        data = await request.json()
        
        farmer_fields = {}
        allowed_fields = ['location', 'latitude', 'longitude', 'land_area_hectares',
                         'crops_grown', 'experience_years', 'bank_account',
                         'bank_ifsc', 'bank_name', 'aadhar_number', 'pan_number', 'upi_id']
        
        for field in allowed_fields:
            if field in data:
                farmer_fields[field] = data[field]
        
        if farmer_fields:
            Farmer.update(farmer['id'], **farmer_fields)
        
        return {'message': 'Profile updated successfully'}
    
    except Exception as e:
        print(f"Update profile error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})
