"""
Admin Module - User Management, Product Approval, Analytics
FastAPI APIRouter (converted from Flask Blueprint)
"""

from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import JSONResponse
from utils.jwt_utils import get_current_user
from models.models import (
    User, Farmer, Buyer, Admin, Product, Order, Payment, Review, Notification,
    BaseModel
)
from datetime import datetime, timedelta
from decimal import Decimal
import json

admin_router = APIRouter(prefix="/api/admin", tags=["admin"])

# ============================================================================
# HELPER - Verify admin & serialize
# ============================================================================

def _check_admin(user_id):
    """Check if current user is admin. Returns admin dict or None."""
    try:
        admin = BaseModel.execute_query(
            "SELECT *, admin_id as id FROM admins WHERE admin_id = %s",
            (int(user_id),), fetch_one=True
        )
        return admin
    except Exception:
        return None

def _serialize(rows):
    """Serialize list of dicts — convert datetime/Decimal for JSON."""
    if not rows:
        return []
    result = []
    for row in rows:
        out = {}
        for k, v in row.items():
            if isinstance(v, datetime):
                out[k] = v.isoformat()
            elif isinstance(v, Decimal):
                out[k] = float(v)
            else:
                out[k] = v
        result.append(out)
    return result

def _serialize_one(row):
    """Serialize a single dict."""
    if not row:
        return row
    out = {}
    for k, v in row.items():
        if isinstance(v, datetime):
            out[k] = v.isoformat()
        elif isinstance(v, Decimal):
            out[k] = float(v)
        else:
            out[k] = v
    return out

# ============================================================================
# DASHBOARD
# ============================================================================

@admin_router.get('/dashboard')
async def dashboard(request: Request, user_id: str = Depends(get_current_user)):
    """Get admin dashboard statistics"""
    try:
        stats = {}

        r = BaseModel.execute_query("SELECT COUNT(*) as cnt FROM farmers", fetch_one=True)
        stats['total_farmers'] = r['cnt'] if r else 0

        r = BaseModel.execute_query("SELECT COUNT(*) as cnt FROM buyers", fetch_one=True)
        stats['total_buyers'] = r['cnt'] if r else 0

        r = BaseModel.execute_query("SELECT COUNT(*) as cnt FROM products", fetch_one=True)
        stats['total_products'] = r['cnt'] if r else 0

        r = BaseModel.execute_query("SELECT COUNT(*) as cnt FROM products WHERE status = 'pending'", fetch_one=True)
        stats['pending_products'] = r['cnt'] if r else 0

        r = BaseModel.execute_query(
            "SELECT COUNT(*) as cnt, COALESCE(SUM(total_amount), 0) as revenue FROM orders",
            fetch_one=True
        )
        stats['total_orders'] = r['cnt'] if r else 0
        stats['total_revenue'] = float(r['revenue'] or 0) if r else 0

        return {
            'success': True,
            'total_users': stats['total_farmers'] + stats['total_buyers'],
            'total_orders': stats['total_orders'],
            'total_revenue': stats['total_revenue'],
            'pending_products': stats['pending_products'],
            'stats': stats
        }

    except Exception as e:
        print(f"Dashboard error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})

# ============================================================================
# USER MANAGEMENT
# ============================================================================

@admin_router.get('/users')
async def get_users(request: Request, user_id: str = Depends(get_current_user)):
    """Get list of all users (farmers + buyers)"""
    try:
        farmers = BaseModel.execute_query(
            "SELECT id, first_name, last_name, email, phone, location, is_active, created_at FROM farmers ORDER BY created_at DESC",
            fetch_all=True
        ) or []

        buyers = BaseModel.execute_query(
            "SELECT id, first_name, last_name, email, phone, location, is_verified, created_at FROM buyers ORDER BY created_at DESC",
            fetch_all=True
        ) or []

        return {
            'success': True,
            'farmers': _serialize(farmers),
            'buyers': _serialize(buyers),
            'total_farmers': len(farmers),
            'total_buyers': len(buyers)
        }

    except Exception as e:
        print(f"Get users error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})


@admin_router.get('/users/{target_user_id}')
async def get_user_details(target_user_id: str, request: Request, user_id: str = Depends(get_current_user)):
    """Get specific user details"""
    try:
        # Try farmer first
        user = BaseModel.execute_query(
            "SELECT *, 'farmer' as role FROM farmers WHERE id = %s",
            (target_user_id,), fetch_one=True
        )
        if not user:
            user = BaseModel.execute_query(
                "SELECT *, 'buyer' as role FROM buyers WHERE id = %s",
                (target_user_id,), fetch_one=True
            )
        if not user:
            return JSONResponse(status_code=404, content={'error': 'User not found'})

        return {'user': _serialize_one(user)}

    except Exception as e:
        print(f"Get user details error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})


@admin_router.post('/users/{target_user_id}/suspend')
async def suspend_user(target_user_id: str, request: Request, user_id: str = Depends(get_current_user)):
    """Suspend user account"""
    try:
        data = await request.json()
        role = data.get('role', '')

        updated = False
        if role == 'farmer' or not role:
            result = BaseModel.execute_query("SELECT id FROM farmers WHERE id = %s", (target_user_id,), fetch_one=True)
            if result:
                BaseModel.execute_query("UPDATE farmers SET is_active = false WHERE id = %s", (target_user_id,))
                updated = True
                role = 'farmer'

        if not updated and (role == 'buyer' or not role):
            result = BaseModel.execute_query("SELECT id FROM buyers WHERE id = %s", (target_user_id,), fetch_one=True)
            if result:
                BaseModel.execute_query("UPDATE buyers SET is_verified = false WHERE id = %s", (target_user_id,))
                updated = True
                role = 'buyer'

        if not updated:
            return JSONResponse(status_code=404, content={'error': 'User not found'})

        # Log action
        try:
            BaseModel.execute_insert(
                """INSERT INTO admin_activity_log (admin_id, action, module, target_id)
                   VALUES (%s, %s, %s, %s)""",
                (int(user_id), 'suspend_user', role, str(target_user_id))
            )
        except Exception:
            pass

        return {'message': 'User suspended successfully'}

    except Exception as e:
        print(f"Suspend user error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})


@admin_router.post('/users/{target_user_id}/activate')
async def activate_user(target_user_id: str, request: Request, user_id: str = Depends(get_current_user)):
    """Activate suspended user"""
    try:
        data = await request.json()
        role = data.get('role', '')

        updated = False
        if role == 'farmer' or not role:
            result = BaseModel.execute_query("SELECT id FROM farmers WHERE id = %s", (target_user_id,), fetch_one=True)
            if result:
                BaseModel.execute_query("UPDATE farmers SET is_active = true WHERE id = %s", (target_user_id,))
                updated = True
                role = 'farmer'

        if not updated and (role == 'buyer' or not role):
            result = BaseModel.execute_query("SELECT id FROM buyers WHERE id = %s", (target_user_id,), fetch_one=True)
            if result:
                BaseModel.execute_query("UPDATE buyers SET is_verified = true WHERE id = %s", (target_user_id,))
                updated = True
                role = 'buyer'

        if not updated:
            return JSONResponse(status_code=404, content={'error': 'User not found'})

        # Log action
        try:
            BaseModel.execute_insert(
                """INSERT INTO admin_activity_log (admin_id, action, module, target_id)
                   VALUES (%s, %s, %s, %s)""",
                (int(user_id), 'activate_user', role, str(target_user_id))
            )
        except Exception:
            pass

        return {'message': 'User activated successfully'}

    except Exception as e:
        print(f"Activate user error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})


@admin_router.post('/users/{target_user_id}/delete')
async def delete_user(target_user_id: str, request: Request, user_id: str = Depends(get_current_user)):
    """Permanently delete user from database"""
    try:
        data = await request.json()
        role = data.get('role', '')

        deleted = False

        if role == 'farmer' or not role:
            result = BaseModel.execute_query(
                "SELECT id, first_name, last_name, email FROM farmers WHERE id = %s",
                (target_user_id,), fetch_one=True
            )
            if result:
                try: BaseModel.execute_query("DELETE FROM products WHERE farmer_id = %s", (target_user_id,))
                except Exception: pass
                try: BaseModel.execute_query("DELETE FROM orders WHERE farmer_id = %s", (target_user_id,))
                except Exception: pass
                try: BaseModel.execute_query("DELETE FROM wallet WHERE farmer_id = %s", (target_user_id,))
                except Exception: pass
                BaseModel.execute_query("DELETE FROM farmers WHERE id = %s", (target_user_id,))
                deleted = True
                role = 'farmer'

        if not deleted and (role == 'buyer' or not role):
            result = BaseModel.execute_query(
                "SELECT id, first_name, last_name, email FROM buyers WHERE id = %s",
                (target_user_id,), fetch_one=True
            )
            if result:
                try: BaseModel.execute_query("DELETE FROM orders WHERE buyer_id = %s", (target_user_id,))
                except Exception: pass
                try: BaseModel.execute_query("DELETE FROM cart WHERE buyer_id = %s", (target_user_id,))
                except Exception: pass
                BaseModel.execute_query("DELETE FROM buyers WHERE id = %s", (target_user_id,))
                deleted = True
                role = 'buyer'

        if not deleted:
            return JSONResponse(status_code=404, content={'error': 'User not found'})

        # Log action
        try:
            BaseModel.execute_insert(
                """INSERT INTO admin_activity_log (admin_id, action, module, target_id)
                   VALUES (%s, %s, %s, %s)""",
                (int(user_id), 'delete_user', role, str(target_user_id))
            )
        except Exception:
            pass

        return {'message': 'User permanently deleted'}

    except Exception as e:
        print(f"Delete user error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})

# ============================================================================
# FARMER VERIFICATION
# ============================================================================

@admin_router.get('/farmers/pending-verification')
async def get_pending_farmers(request: Request, user_id: str = Depends(get_current_user)):
    """Get farmers pending verification"""
    try:
        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 20))
        offset = (page - 1) * limit

        farmers = BaseModel.execute_query(
            """SELECT f.* FROM farmers f
               WHERE f.is_verified = FALSE
               ORDER BY f.created_at ASC LIMIT %s OFFSET %s""",
            (limit, offset), fetch_all=True
        ) or []

        return {'farmers': _serialize(farmers), 'page': page, 'limit': limit}

    except Exception as e:
        print(f"Get pending farmers error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})


@admin_router.post('/farmers/{farmer_id}/verify')
async def verify_farmer(farmer_id: int, request: Request, user_id: str = Depends(get_current_user)):
    """Verify farmer"""
    try:
        farmer = Farmer.get_by_id(farmer_id)
        if not farmer:
            return JSONResponse(status_code=404, content={'error': 'Farmer not found'})

        Farmer.update(farmer_id, is_verified=True)
        return {'message': 'Farmer verified successfully'}

    except Exception as e:
        print(f"Verify farmer error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})


@admin_router.post('/farmers/{farmer_id}/reject')
async def reject_farmer(farmer_id: int, request: Request, user_id: str = Depends(get_current_user)):
    """Reject farmer verification"""
    try:
        farmer = Farmer.get_by_id(farmer_id)
        if not farmer:
            return JSONResponse(status_code=404, content={'error': 'Farmer not found'})

        data = await request.json()
        reason = data.get('reason', 'Verification rejected')

        BaseModel.execute_query(
            "UPDATE farmers SET is_verified = FALSE WHERE id = %s", (farmer_id,)
        )

        return {'message': 'Farmer verification rejected'}

    except Exception as e:
        print(f"Reject farmer error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})

# ============================================================================
# PRODUCT MODERATION
# ============================================================================

@admin_router.get('/products/all')
async def get_all_products(request: Request, user_id: str = Depends(get_current_user)):
    """Get ALL products for admin management"""
    try:
        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 100))
        offset = (page - 1) * limit
        status_filter = request.query_params.get('status', '')

        query = """
        SELECT p.*, f.first_name, f.last_name, f.phone as farmer_phone, f.email as farmer_email
        FROM products p
        LEFT JOIN farmers f ON p.farmer_id = f.id
        """
        params = []
        if status_filter:
            query += " WHERE p.status = %s"
            params.append(status_filter)
        query += " ORDER BY p.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        products = BaseModel.execute_query(query, tuple(params), fetch_all=True) or []

        return {'products': _serialize(products), 'total': len(products)}

    except Exception as e:
        import traceback; traceback.print_exc()
        return JSONResponse(status_code=500, content={'error': str(e)})


@admin_router.get('/products/pending-approval')
async def get_pending_products(request: Request, user_id: str = Depends(get_current_user)):
    """Get products pending approval"""
    try:
        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 50))
        offset = (page - 1) * limit

        products = BaseModel.execute_query(
            """SELECT p.*, f.first_name, f.last_name, f.phone as farmer_phone
               FROM products p
               LEFT JOIN farmers f ON p.farmer_id = f.id
               WHERE p.status = 'pending'
               ORDER BY p.created_at ASC LIMIT %s OFFSET %s""",
            (limit, offset), fetch_all=True
        ) or []

        return {'products': _serialize(products), 'page': page, 'limit': limit}

    except Exception as e:
        import traceback; traceback.print_exc()
        return JSONResponse(status_code=500, content={'error': str(e)})


@admin_router.post('/products/{product_id}/approve')
async def approve_product(product_id: int, request: Request, user_id: str = Depends(get_current_user)):
    """Approve product"""
    try:
        product = BaseModel.execute_query(
            "SELECT id, name FROM products WHERE id = %s", (product_id,), fetch_one=True
        )
        if not product:
            return JSONResponse(status_code=404, content={'error': 'Product not found'})

        BaseModel.execute_query("UPDATE products SET status = 'approved' WHERE id = %s", (product_id,))
        return {'message': f'Product "{product["name"]}" approved successfully'}

    except Exception as e:
        import traceback; traceback.print_exc()
        return JSONResponse(status_code=500, content={'error': str(e)})


@admin_router.post('/products/{product_id}/reject')
async def reject_product(product_id: int, request: Request, user_id: str = Depends(get_current_user)):
    """Reject product"""
    try:
        product = BaseModel.execute_query(
            "SELECT id, name FROM products WHERE id = %s", (product_id,), fetch_one=True
        )
        if not product:
            return JSONResponse(status_code=404, content={'error': 'Product not found'})

        BaseModel.execute_query("UPDATE products SET status = 'rejected' WHERE id = %s", (product_id,))
        return {'message': f'Product "{product["name"]}" rejected'}

    except Exception as e:
        import traceback; traceback.print_exc()
        return JSONResponse(status_code=500, content={'error': str(e)})

# ============================================================================
# ANALYTICS
# ============================================================================

@admin_router.get('/analytics/revenue')
async def analytics_revenue(request: Request, user_id: str = Depends(get_current_user)):
    """Get revenue analytics"""
    try:
        days = int(request.query_params.get('days', 30))
        start_date = datetime.now() - timedelta(days=days)

        analytics = BaseModel.execute_query(
            """SELECT DATE(o.created_at) as date, SUM(o.total_amount) as daily_revenue, COUNT(*) as order_count
               FROM orders o
               WHERE o.created_at >= %s AND o.status = 'delivered'
               GROUP BY DATE(o.created_at)
               ORDER BY date DESC""",
            (start_date,), fetch_all=True
        ) or []

        return {'period_days': days, 'analytics': _serialize(analytics)}

    except Exception as e:
        print(f"Analytics revenue error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})


@admin_router.get('/analytics/orders')
async def analytics_orders(request: Request, user_id: str = Depends(get_current_user)):
    """Get orders analytics"""
    try:
        days = int(request.query_params.get('days', 30))
        start_date = datetime.now() - timedelta(days=days)

        analytics = BaseModel.execute_query(
            """SELECT status, COUNT(*) as count,
                      AVG(total_amount) as avg_price, SUM(total_amount) as total_price
               FROM orders WHERE created_at >= %s GROUP BY status""",
            (start_date,), fetch_all=True
        ) or []

        return {'period_days': days, 'analytics': _serialize(analytics)}

    except Exception as e:
        print(f"Analytics orders error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})


@admin_router.get('/analytics/users')
async def analytics_users(request: Request, user_id: str = Depends(get_current_user)):
    """Get users growth analytics"""
    try:
        days = int(request.query_params.get('days', 30))
        start_date = datetime.now() - timedelta(days=days)

        farmer_count = BaseModel.execute_query(
            "SELECT COUNT(*) as count FROM farmers WHERE created_at >= %s",
            (start_date,), fetch_one=True
        )
        buyer_count = BaseModel.execute_query(
            "SELECT COUNT(*) as count FROM buyers WHERE created_at >= %s",
            (start_date,), fetch_one=True
        )

        analytics = [
            {'role_name': 'farmer', 'count': farmer_count['count'] if farmer_count else 0},
            {'role_name': 'buyer', 'count': buyer_count['count'] if buyer_count else 0}
        ]

        return {'period_days': days, 'analytics': analytics}

    except Exception as e:
        print(f"Analytics users error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})

# ============================================================================
# DISPUTES
# ============================================================================

@admin_router.get('/disputes')
async def get_disputes(request: Request, user_id: str = Depends(get_current_user)):
    """Get disputes/complaints"""
    try:
        status = request.query_params.get('status', 'open')
        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 20))
        offset = (page - 1) * limit

        try:
            disputes = BaseModel.execute_query(
                "SELECT * FROM disputes WHERE status = %s ORDER BY created_at DESC LIMIT %s OFFSET %s",
                (status, limit, offset), fetch_all=True
            ) or []
        except Exception:
            disputes = []

        return {'disputes': _serialize(disputes), 'page': page, 'limit': limit}

    except Exception as e:
        print(f"Get disputes error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})


@admin_router.post('/disputes/{dispute_id}/resolve')
async def resolve_dispute(dispute_id: int, request: Request, user_id: str = Depends(get_current_user)):
    """Resolve dispute"""
    try:
        data = await request.json()
        resolution = data.get('resolution', '')

        try:
            BaseModel.execute_query(
                "UPDATE disputes SET status = %s, resolution = %s WHERE id = %s",
                ('resolved', resolution, dispute_id)
            )
        except Exception:
            pass

        return {'message': 'Dispute resolved successfully'}

    except Exception as e:
        print(f"Resolve dispute error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})

# ============================================================================
# AUDIT LOG
# ============================================================================

@admin_router.get('/audit-logs')
async def get_audit_logs(request: Request, user_id: str = Depends(get_current_user)):
    """Get audit logs"""
    try:
        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 50))
        offset = (page - 1) * limit

        try:
            logs = BaseModel.execute_query(
                "SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT %s OFFSET %s",
                (limit, offset), fetch_all=True
            ) or []
        except Exception:
            logs = []

        return {'logs': _serialize(logs), 'page': page, 'limit': limit}

    except Exception as e:
        print(f"Get audit logs error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})

# ============================================================================
# ACTIVITY FEED
# ============================================================================

@admin_router.get('/activity-feed')
async def get_activity_feed(request: Request, user_id: str = Depends(get_current_user)):
    """Get recent platform activity"""
    try:
        limit = int(request.query_params.get('limit', 20))
        activities = []

        # Recent orders
        try:
            orders = BaseModel.execute_query(
                """SELECT o.id, o.status, o.total_amount, o.created_at,
                          p.name as product_name,
                          f.first_name as farmer_first_name, f.last_name as farmer_last_name
                   FROM orders o
                   LEFT JOIN products p ON o.product_id = p.id
                   LEFT JOIN farmers f ON o.farmer_id = f.id
                   ORDER BY o.created_at DESC LIMIT %s""",
                (limit,), fetch_all=True
            ) or []
            for o in orders:
                activities.append({
                    'type': 'order',
                    'message': f"New order for {o.get('product_name', 'product')} - Status: {o.get('status', 'pending')}",
                    'amount': float(o['total_amount']) if o.get('total_amount') else 0,
                    'timestamp': o['created_at'].isoformat() if o.get('created_at') else None
                })
        except Exception:
            pass

        # Recent farmers
        try:
            new_farmers = BaseModel.execute_query(
                "SELECT id, first_name, last_name, email, created_at FROM farmers ORDER BY created_at DESC LIMIT 5",
                fetch_all=True
            ) or []
            for f in new_farmers:
                activities.append({
                    'type': 'new_farmer',
                    'message': f"New farmer registered: {f.get('first_name', '')} {f.get('last_name', '')}",
                    'timestamp': f['created_at'].isoformat() if f.get('created_at') else None
                })
        except Exception:
            pass

        # Sort by timestamp
        activities.sort(key=lambda x: x.get('timestamp') or '', reverse=True)

        return {'activities': activities[:limit]}

    except Exception as e:
        print(f"Activity feed error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})

# ============================================================================
# RECEIPTS
# ============================================================================

@admin_router.get('/receipts')
async def get_all_receipts(request: Request, user_id: str = Depends(get_current_user)):
    """Get all payment receipts"""
    try:
        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 50))
        offset = (page - 1) * limit

        try:
            receipts = BaseModel.execute_query(
                """SELECT 
                    r.id,
                    r.receipt_id,
                    r.grand_total as total_amount,
                    r.grand_total,
                    r.payment_type,
                    r.created_at,
                    COALESCE(r.buyer_name, CONCAT(b.first_name, ' ', b.last_name)) as buyer_name,
                    CONCAT(f.first_name, ' ', f.last_name) as farmer_name,
                    COALESCE(
                        (SELECT STRING_AGG(ri.product_name, ', ') FROM receipt_items ri WHERE ri.receipt_id = r.id),
                        'N/A'
                    ) as product_name,
                    COALESCE(
                        (SELECT SUM(ri.quantity_kg) FROM receipt_items ri WHERE ri.receipt_id = r.id),
                        0
                    ) as quantity_kg
                   FROM receipts r
                   LEFT JOIN farmers f ON r.farmer_id = f.id
                   LEFT JOIN buyers b ON r.buyer_id = b.id
                   ORDER BY r.created_at DESC LIMIT %s OFFSET %s""",
                (limit, offset), fetch_all=True
            ) or []
        except Exception as query_err:
            print(f"Error executing receipts query: {query_err}")
            receipts = []

        return {'receipts': _serialize(receipts), 'total': len(receipts)}

    except Exception as e:
        print(f"Get receipts error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})

# ============================================================================
# FARMER / BUYER PROFILES (Admin view)
# ============================================================================

@admin_router.get('/farmer-profiles')
async def get_farmer_profiles(request: Request, user_id: str = Depends(get_current_user)):
    """Get all farmer profiles for admin"""
    try:
        farmers = BaseModel.execute_query(
            """SELECT f.*, COUNT(DISTINCT p.id) as product_count,
                      COUNT(DISTINCT o.id) as order_count
               FROM farmers f
               LEFT JOIN products p ON f.id = p.farmer_id
               LEFT JOIN orders o ON f.id = o.farmer_id
               GROUP BY f.id
               ORDER BY f.created_at DESC""",
            fetch_all=True
        ) or []

        return {'farmers': _serialize(farmers)}

    except Exception as e:
        print(f"Get farmer profiles error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})


@admin_router.get('/buyer-profiles')
async def get_buyer_profiles(request: Request, user_id: str = Depends(get_current_user)):
    """Get all buyer profiles for admin"""
    try:
        buyers = BaseModel.execute_query(
            """SELECT b.*, COUNT(DISTINCT o.id) as order_count,
                      COALESCE(SUM(o.total_amount), 0) as total_spent
               FROM buyers b
               LEFT JOIN orders o ON b.id = o.buyer_id
               GROUP BY b.id
               ORDER BY b.created_at DESC""",
            fetch_all=True
        ) or []

        return {'buyers': _serialize(buyers)}

    except Exception as e:
        print(f"Get buyer profiles error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})

# ============================================================================
# PLATFORM EARNINGS
# ============================================================================

@admin_router.get('/platform-earnings')
async def get_platform_earnings(request: Request, user_id: str = Depends(get_current_user)):
    """Get platform earnings breakdown"""
    try:
        try:
            earnings = BaseModel.execute_query(
                "SELECT * FROM platform_earnings ORDER BY created_at DESC LIMIT 50",
                fetch_all=True
            ) or []
        except Exception:
            earnings = []

        return {'earnings': _serialize(earnings)}

    except Exception as e:
        print(f"Get platform earnings error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})


@admin_router.post('/platform-earnings/{earning_id}/settle')
async def settle_earning(earning_id: int, request: Request, user_id: str = Depends(get_current_user)):
    """Mark earning as settled"""
    try:
        try:
            BaseModel.execute_query(
                "UPDATE platform_earnings SET settlement_status = 'settled', settled_at = NOW() WHERE id = %s",
                (earning_id,)
            )
        except Exception:
            pass

        return {'success': True, 'message': 'Marked as settled'}

    except Exception as e:
        print(f"Settle earning error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})

# ============================================================================
# SaaS ANALYTICS (frontend expects these) - Commented out to use saas_dashboard.py implementations
# ============================================================================

# @admin_router.get('/saas/analytics')
# async def saas_analytics(request: Request, user_id: str = Depends(get_current_user)):
#     """SaaS analytics overview"""
#     try:
#         return {'revenue': 0, 'orders': 0, 'users': 0, 'products': 0}
#     except Exception as e:
#         return JSONResponse(status_code=500, content={'error': str(e)})

# @admin_router.get('/saas/top-products')
# async def saas_top_products(request: Request, user_id: str = Depends(get_current_user)):
#     """Top products"""
#     return []

# @admin_router.get('/saas/revenue-breakdown')
# async def saas_revenue_breakdown(request: Request, user_id: str = Depends(get_current_user)):
#     """Revenue breakdown"""
#     return []

# @admin_router.get('/saas/monthly-sales')
# async def saas_monthly_sales(request: Request, user_id: str = Depends(get_current_user)):
#     """Monthly sales"""
#     return []

# @admin_router.get('/saas/profile')
# async def saas_profile(request: Request, user_id: str = Depends(get_current_user)):
#     """Admin profile"""
#     try:
#         admin = _check_admin(user_id)
#         return admin or {'id': user_id, 'role': 'admin'}
#     except Exception:
#         return {}
