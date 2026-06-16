"""
Admin Module - User Management, Product Approval, Analytics
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.models import (
    User, Farmer, Buyer, Admin, Product, Order, Payment, Review, Notification,
    BaseModel
)
from datetime import datetime, timedelta
import json

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# ============================================================================
# MIDDLEWARE - Verify User is Admin
# ============================================================================

def admin_required(f):
    """Decorator to ensure user is admin"""
    def decorated_function(*args, **kwargs):
        user_id = get_jwt_identity()
        admin = BaseModel.execute_query("SELECT *, admin_id as id FROM admins WHERE admin_id = %s", (int(user_id),), fetch_one=True)
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        kwargs['admin'] = admin
        return f(*args, **kwargs)
    
    decorated_function.__name__ = f.__name__
    return decorated_function

# ============================================================================
# DASHBOARD
# ============================================================================

@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard():
    """Get admin dashboard statistics"""
    try:
        user_id = get_jwt_identity()
        admin = BaseModel.execute_query("SELECT *, admin_id as id FROM admins WHERE admin_id = %s", (int(user_id),), fetch_one=True)
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        stats = {}
        
        # Farmer count
        r = BaseModel.execute_query("SELECT COUNT(*) as cnt FROM farmers", fetch_one=True)
        stats['total_farmers'] = r['cnt'] if r else 0
        
        # Buyer count
        r = BaseModel.execute_query("SELECT COUNT(*) as cnt FROM buyers", fetch_one=True)
        stats['total_buyers'] = r['cnt'] if r else 0
        
        # Product count
        r = BaseModel.execute_query("SELECT COUNT(*) as cnt FROM products", fetch_one=True)
        stats['total_products'] = r['cnt'] if r else 0
        
        # Pending products
        r = BaseModel.execute_query("SELECT COUNT(*) as cnt FROM products WHERE status = 'pending'", fetch_one=True)
        stats['pending_products'] = r['cnt'] if r else 0
        
        # Order stats
        r = BaseModel.execute_query("SELECT COUNT(*) as cnt, COALESCE(SUM(total_amount), 0) as revenue FROM orders", fetch_one=True)
        stats['total_orders'] = r['cnt'] if r else 0
        stats['total_revenue'] = float(r['revenue'] or 0) if r else 0
        
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
    
    except Exception as e:
        print(f"Dashboard error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# USER MANAGEMENT
# ============================================================================

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    """Get list of all users"""
    try:
        user_id = get_jwt_identity()
        admin = BaseModel.execute_query("SELECT *, admin_id as id FROM admins WHERE admin_id = %s", (int(user_id),), fetch_one=True)
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        farmers = BaseModel.execute_query(
            "SELECT id, first_name, last_name, email, phone, location, status, created_at FROM farmers ORDER BY created_at DESC",
            fetch_all=True
        ) or []
        
        buyers = BaseModel.execute_query(
            "SELECT id, first_name, last_name, email, phone, location, status, created_at FROM buyers ORDER BY created_at DESC",
            fetch_all=True
        ) or []
        
        return jsonify({
            'success': True,
            'farmers': farmers,
            'buyers': buyers,
            'total_farmers': len(farmers),
            'total_buyers': len(buyers)
        }), 200
    
    except Exception as e:
        print(f"Get users error: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_details(user_id):
    """Get specific user details"""
    try:
        admin_user_id = get_jwt_identity()
        admin = BaseModel.execute_query("SELECT *, admin_id as id FROM admins WHERE admin_id = %s", (int(admin_user_id),), fetch_one=True)
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        user = BaseModel.execute_query("SELECT * FROM farmers WHERE id = %s UNION SELECT * FROM buyers WHERE id = %s", (user_id, user_id), fetch_one=True)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get role-specific details
        role_details = {}
        if user['role_name'] == 'farmer':
            farmer = Farmer.get_by_user_id(user_id)
            role_details = farmer
        elif user['role_name'] == 'buyer':
            buyer = Buyer.get_by_user_id(user_id)
            role_details = buyer
        
        return jsonify({
            'user': user,
            'role_details': role_details
        }), 200
    
    except Exception as e:
        print(f"Get user details error: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>/suspend', methods=['POST'])
@jwt_required()
def suspend_user(user_id):
    """Suspend user account"""
    try:
        admin_user_id = get_jwt_identity()
        admin = BaseModel.execute_query("SELECT *, admin_id as id FROM admins WHERE admin_id = %s", (int(admin_user_id),), fetch_one=True)
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json() or {}
        role = data.get('role', '')
        reason = data.get('reason', 'Account suspended by admin')
        
        # Try to find the user in farmers or buyers
        updated = False
        if role == 'farmer' or not role:
            result = BaseModel.execute_query("SELECT id FROM farmers WHERE id = %s", (user_id,), fetch_one=True)
            if result:
                BaseModel.execute_query("UPDATE farmers SET status = 'suspended' WHERE id = %s", (user_id,))
                updated = True
                role = 'farmer'
        
        if not updated and (role == 'buyer' or not role):
            result = BaseModel.execute_query("SELECT id FROM buyers WHERE id = %s", (user_id,), fetch_one=True)
            if result:
                BaseModel.execute_query("UPDATE buyers SET status = 'suspended' WHERE id = %s", (user_id,))
                updated = True
                role = 'buyer'
        
        if not updated:
            return jsonify({'error': 'User not found'}), 404
        
        # Log the action
        try:
            BaseModel.execute_insert(
                """INSERT INTO admin_activity_log (admin_id, action, module, target_id, details)
                   VALUES (%s, %s, %s, %s, %s)""",
                (admin_user_id, 'suspend_user', role, str(user_id), reason)
            )
        except Exception:
            pass  # Non-critical
        
        return jsonify({'message': 'User suspended successfully'}), 200
    
    except Exception as e:
        print(f"Suspend user error: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>/activate', methods=['POST'])
@jwt_required()
def activate_user(user_id):
    """Activate suspended user"""
    try:
        admin_user_id = get_jwt_identity()
        admin = BaseModel.execute_query("SELECT *, admin_id as id FROM admins WHERE admin_id = %s", (int(admin_user_id),), fetch_one=True)
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json() or {}
        role = data.get('role', '')
        
        updated = False
        if role == 'farmer' or not role:
            result = BaseModel.execute_query("SELECT id FROM farmers WHERE id = %s", (user_id,), fetch_one=True)
            if result:
                BaseModel.execute_query("UPDATE farmers SET status = 'active' WHERE id = %s", (user_id,))
                updated = True
                role = 'farmer'
        
        if not updated and (role == 'buyer' or not role):
            result = BaseModel.execute_query("SELECT id FROM buyers WHERE id = %s", (user_id,), fetch_one=True)
            if result:
                BaseModel.execute_query("UPDATE buyers SET status = 'active' WHERE id = %s", (user_id,))
                updated = True
                role = 'buyer'
        
        if not updated:
            return jsonify({'error': 'User not found'}), 404
        
        # Log the action
        try:
            BaseModel.execute_insert(
                """INSERT INTO admin_activity_log (admin_id, action, module, target_id, details)
                   VALUES (%s, %s, %s, %s, %s)""",
                (admin_user_id, 'activate_user', role, str(user_id), 'Account reactivated')
            )
        except Exception:
            pass
        
        return jsonify({'message': 'User activated successfully'}), 200
    
    except Exception as e:
        print(f"Activate user error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# FARMER VERIFICATION
# ============================================================================

@admin_bp.route('/farmers/pending-verification', methods=['GET'])
@jwt_required()
def get_pending_farmers():
    """Get farmers pending verification"""
    try:
        admin_user_id = get_jwt_identity()
        admin = BaseModel.execute_query("SELECT *, admin_id as id FROM admins WHERE admin_id = %s", (int(admin_user_id),), fetch_one=True)
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        offset = (page - 1) * limit
        
        query = """
        SELECT f.*, u.email, u.phone, u.first_name, u.last_name
        FROM farmers f
        LEFT JOIN users u ON f.user_id = u.id
        WHERE f.is_verified = FALSE
        ORDER BY f.created_at ASC
        LIMIT %s OFFSET %s
        """
        
        farmers = BaseModel.execute_query(query, (limit, offset), fetch_all=True)
        
        return jsonify({
            'farmers': farmers,
            'page': page,
            'limit': limit
        }), 200
    
    except Exception as e:
        print(f"Get pending farmers error: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/farmers/<int:farmer_id>/verify', methods=['POST'])
@jwt_required()
def verify_farmer(farmer_id):
    """Verify farmer"""
    try:
        admin_user_id = get_jwt_identity()
        admin = BaseModel.execute_query("SELECT *, admin_id as id FROM admins WHERE admin_id = %s", (int(admin_user_id),), fetch_one=True)
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        farmer = Farmer.get_by_id(farmer_id)
        if not farmer:
            return jsonify({'error': 'Farmer not found'}), 404
        
        Farmer.update(farmer_id, is_verified=True, verification_date=datetime.now())
        
        # Record in audit log
        BaseModel.execute_insert(
            """INSERT INTO audit_logs (admin_id, action, target_user_id, details)
               VALUES (%s, %s, %s, %s)""",
            (admin_user_id, 'verify_farmer', farmer['user_id'], f'Farmer {farmer_id} verified')
        )
        
        # Notify farmer
        Notification.create(
            user_id=farmer['user_id'],
            title='Account Verified',
            message='Your farmer account has been verified!',
            notification_type='system'
        )
        
        return jsonify({'message': 'Farmer verified successfully'}), 200
    
    except Exception as e:
        print(f"Verify farmer error: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/farmers/<int:farmer_id>/reject', methods=['POST'])
@jwt_required()
def reject_farmer(farmer_id):
    """Reject farmer verification"""
    try:
        admin_user_id = get_jwt_identity()
        admin = BaseModel.execute_query("SELECT *, admin_id as id FROM admins WHERE admin_id = %s", (int(admin_user_id),), fetch_one=True)
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        farmer = Farmer.get_by_id(farmer_id)
        if not farmer:
            return jsonify({'error': 'Farmer not found'}), 404
        
        data = request.get_json()
        reason = data.get('reason', 'Verification rejected')
        
        BaseModel.execute_query(
            "UPDATE farmers SET is_verified = FALSE, verification_notes = %s WHERE id = %s",
            (reason, farmer_id)
        )
        
        # Record in audit log
        BaseModel.execute_insert(
            """INSERT INTO audit_logs (admin_id, action, target_user_id, details)
               VALUES (%s, %s, %s, %s)""",
            (admin_user_id, 'reject_farmer', farmer['user_id'], reason)
        )
        
        # Notify farmer
        Notification.create(
            user_id=farmer['user_id'],
            title='Verification Rejected',
            message=f'Your farmer account verification was rejected. Reason: {reason}',
            notification_type='system'
        )
        
        return jsonify({'message': 'Farmer verification rejected'}), 200
    
    except Exception as e:
        print(f"Reject farmer error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# PRODUCT MODERATION
# ============================================================================

@admin_bp.route('/products/all', methods=['GET'])
@jwt_required()
def get_all_products():
    """Get ALL products for admin management"""
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 100, type=int)
        offset = (page - 1) * limit
        status_filter = request.args.get('status', '')

        query = """
        SELECT p.*, f.first_name, f.last_name, f.phone as farmer_phone, f.email as farmer_email
        FROM products p
        LEFT JOIN farmers f ON p.farmer_id = f.id
        """
        params = []
        if status_filter:
            query += " WHERE p.approval_status = %s"
            params.append(status_filter)
        query += " ORDER BY p.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        products = BaseModel.execute_query(query, tuple(params), fetch_all=True) or []

        # Serialize datetime and Decimal fields
        from datetime import datetime as dt
        from decimal import Decimal
        serialized = []
        for p in products:
            row = {}
            for k, v in p.items():
                if isinstance(v, dt):
                    row[k] = v.isoformat()
                elif isinstance(v, Decimal):
                    row[k] = float(v)
                else:
                    row[k] = v
            serialized.append(row)

        return jsonify({
            'products': serialized,
            'total': len(serialized),
        }), 200

    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/products/pending-approval', methods=['GET'])
@jwt_required()
def get_pending_products():
    """Get products pending approval"""
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 50, type=int)
        offset = (page - 1) * limit

        query = """
        SELECT p.*, f.first_name, f.last_name, f.phone as farmer_phone
        FROM products p
        LEFT JOIN farmers f ON p.farmer_id = f.id
        WHERE p.approval_status = 'pending'
        ORDER BY p.created_at ASC
        LIMIT %s OFFSET %s
        """

        products = BaseModel.execute_query(query, (limit, offset), fetch_all=True) or []

        from datetime import datetime as dt
        from decimal import Decimal
        serialized = []
        for p in products:
            row = {}
            for k, v in p.items():
                if isinstance(v, dt):
                    row[k] = v.isoformat()
                elif isinstance(v, Decimal):
                    row[k] = float(v)
                else:
                    row[k] = v
            serialized.append(row)

        return jsonify({
            'products': serialized,
            'page': page,
            'limit': limit
        }), 200

    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/products/<int:product_id>/approve', methods=['POST'])
@jwt_required()
def approve_product(product_id):
    """Approve product"""
    try:
        # Check product exists
        product = BaseModel.execute_query(
            "SELECT id, name, farmer_id FROM products WHERE id = %s", (product_id,), fetch_one=True
        )
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        # Update approval_status
        BaseModel.execute_query(
            "UPDATE products SET approval_status = 'approved', status = 'approved' WHERE id = %s",
            (product_id,)
        )

        # Log activity
        try:
            admin_user_id = get_jwt_identity()
            BaseModel.execute_query(
                "INSERT INTO admin_activity_log (admin_id, action, details) VALUES (%s, %s, %s)",
                (int(admin_user_id), 'approve_product', f'Product {product_id} ({product["name"]}) approved')
            )
        except:
            pass

        return jsonify({'message': f'Product "{product["name"]}" approved successfully'}), 200

    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/products/<int:product_id>/reject', methods=['POST'])
@jwt_required()
def reject_product(product_id):
    """Reject product"""
    try:
        product = BaseModel.execute_query(
            "SELECT id, name, farmer_id FROM products WHERE id = %s", (product_id,), fetch_one=True
        )
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        data = request.get_json() or {}
        reason = data.get('reason', 'Product does not meet guidelines')

        BaseModel.execute_query(
            "UPDATE products SET approval_status = 'rejected', status = 'rejected', rejection_reason = %s WHERE id = %s",
            (reason, product_id)
        )

        try:
            admin_user_id = get_jwt_identity()
            BaseModel.execute_query(
                "INSERT INTO admin_activity_log (admin_id, action, details) VALUES (%s, %s, %s)",
                (int(admin_user_id), 'reject_product', f'Product {product_id} ({product["name"]}) rejected: {reason}')
            )
        except:
            pass

        return jsonify({'message': f'Product "{product["name"]}" rejected'}), 200

    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ============================================================================
# ANALYTICS
# ============================================================================

@admin_bp.route('/analytics/revenue', methods=['GET'])
@jwt_required()
def analytics_revenue():
    """Get revenue analytics"""
    try:
        admin_user_id = get_jwt_identity()
        admin = BaseModel.execute_query("SELECT *, admin_id as id FROM admins WHERE admin_id = %s", (int(admin_user_id),), fetch_one=True)
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        days = request.args.get('days', 30, type=int)
        start_date = datetime.now() - timedelta(days=days)
        
        query = """
        SELECT DATE(o.created_at) as date, SUM(o.final_price) as daily_revenue, COUNT(*) as order_count
        FROM orders o
        WHERE o.created_at >= %s AND o.status = 'delivered'
        GROUP BY DATE(o.created_at)
        ORDER BY date DESC
        """
        
        analytics = BaseModel.execute_query(query, (start_date,), fetch_all=True)
        
        return jsonify({
            'period_days': days,
            'analytics': analytics
        }), 200
    
    except Exception as e:
        print(f"Analytics revenue error: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/analytics/orders', methods=['GET'])
@jwt_required()
def analytics_orders():
    """Get orders analytics"""
    try:
        admin_user_id = get_jwt_identity()
        admin = BaseModel.execute_query("SELECT *, admin_id as id FROM admins WHERE admin_id = %s", (int(admin_user_id),), fetch_one=True)
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        days = request.args.get('days', 30, type=int)
        start_date = datetime.now() - timedelta(days=days)
        
        query = """
        SELECT 
            status,
            COUNT(*) as count,
            AVG(final_price) as avg_price,
            SUM(final_price) as total_price
        FROM orders
        WHERE created_at >= %s
        GROUP BY status
        """
        
        analytics = BaseModel.execute_query(query, (start_date,), fetch_all=True)
        
        return jsonify({
            'period_days': days,
            'analytics': analytics
        }), 200
    
    except Exception as e:
        print(f"Analytics orders error: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/analytics/users', methods=['GET'])
@jwt_required()
def analytics_users():
    """Get users growth analytics"""
    try:
        admin_user_id = get_jwt_identity()
        admin = BaseModel.execute_query("SELECT *, admin_id as id FROM admins WHERE admin_id = %s", (int(admin_user_id),), fetch_one=True)
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        days = request.args.get('days', 30, type=int)
        start_date = datetime.now() - timedelta(days=days)
        
        query = """
        SELECT 
            role_name,
            COUNT(*) as count
        FROM users
        WHERE created_at >= %s
        GROUP BY role_name
        """
        
        analytics = BaseModel.execute_query(query, (start_date,), fetch_all=True)
        
        return jsonify({
            'period_days': days,
            'analytics': analytics
        }), 200
    
    except Exception as e:
        print(f"Analytics users error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# DISPUTE RESOLUTION
# ============================================================================

@admin_bp.route('/disputes', methods=['GET'])
@jwt_required()
def get_disputes():
    """Get disputes/complaints"""
    try:
        admin_user_id = get_jwt_identity()
        admin = BaseModel.execute_query("SELECT *, admin_id as id FROM admins WHERE admin_id = %s", (int(admin_user_id),), fetch_one=True)
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        status = request.args.get('status', 'open')
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        offset = (page - 1) * limit
        
        query = """
        SELECT * FROM disputes
        WHERE status = %s
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """
        
        disputes = BaseModel.execute_query(query, (status, limit, offset), fetch_all=True)
        
        return jsonify({
            'disputes': disputes,
            'page': page,
            'limit': limit
        }), 200
    
    except Exception as e:
        print(f"Get disputes error: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/disputes/<int:dispute_id>/resolve', methods=['POST'])
@jwt_required()
def resolve_dispute(dispute_id):
    """Resolve dispute"""
    try:
        admin_user_id = get_jwt_identity()
        admin = BaseModel.execute_query("SELECT *, admin_id as id FROM admins WHERE admin_id = %s", (int(admin_user_id),), fetch_one=True)
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        resolution = data.get('resolution', '')
        
        BaseModel.execute_query(
            "UPDATE disputes SET status = %s, resolution = %s, resolved_at = %s WHERE id = %s",
            ('resolved', resolution, datetime.now(), dispute_id)
        )
        
        return jsonify({'message': 'Dispute resolved successfully'}), 200
    
    except Exception as e:
        print(f"Resolve dispute error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# AUDIT LOG
# ============================================================================

@admin_bp.route('/audit-logs', methods=['GET'])
@jwt_required()
def get_audit_logs():
    """Get audit logs"""
    try:
        admin_user_id = get_jwt_identity()
        admin = BaseModel.execute_query("SELECT *, admin_id as id FROM admins WHERE admin_id = %s", (int(admin_user_id),), fetch_one=True)
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 50, type=int)
        offset = (page - 1) * limit
        
        query = """
        SELECT * FROM audit_logs
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """
        
        logs = BaseModel.execute_query(query, (limit, offset), fetch_all=True)
        
        return jsonify({
            'logs': logs,
            'page': page,
            'limit': limit
        }), 200
    
    except Exception as e:
        print(f"Get audit logs error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# HELPER - Serialize datetime and Decimal for JSON
# ============================================================================

from datetime import datetime as dt
from decimal import Decimal

def serialize_row(row):
    """Serialize a single row dict, converting datetime and Decimal fields."""
    if not row:
        return row
    out = {}
    for k, v in row.items():
        if isinstance(v, dt):
            out[k] = v.isoformat()
        elif isinstance(v, Decimal):
            out[k] = float(v)
        else:
            out[k] = v
    return out

def serialize_rows(rows):
    """Serialize a list of row dicts."""
    if not rows:
        return []
    return [serialize_row(r) for r in rows]

# ============================================================================
# ACTIVITY FEED / LIVE MONITORING
# ============================================================================

@admin_bp.route('/activity-feed', methods=['GET'])
@jwt_required()
def get_activity_feed():
    """Get combined activity feed of recent activities across the platform"""
    try:
        user_id = get_jwt_identity()
        admin = BaseModel.execute_query(
            "SELECT *, admin_id as id FROM admins WHERE admin_id = %s",
            (int(user_id),), fetch_one=True
        )
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403

        activities = []

        # 1. Recent product listings
        try:
            products = BaseModel.execute_query(
                """SELECT p.id, p.name, p.farmer_id, p.category, p.price, p.created_at,
                          f.first_name as farmer_first, f.last_name as farmer_last
                   FROM products p
                   LEFT JOIN farmers f ON p.farmer_id = f.id
                   ORDER BY p.created_at DESC LIMIT 20""",
                fetch_all=True
            ) or []
            for p in products:
                p = serialize_row(p)
                farmer_name = f"{p.get('farmer_first', '')} {p.get('farmer_last', '')}".strip() or 'Unknown Farmer'
                activities.append({
                    'type': 'product_listed',
                    'message': f"{farmer_name} listed {p.get('name', 'a product')} at ₹{p.get('price', 0)}/{p.get('category', 'kg')}",
                    'timestamp': p.get('created_at', ''),
                    'details': p
                })
        except Exception as e:
            print(f"Activity feed - products error: {e}")

        # 2. Recent receipts/purchases
        try:
            receipts = BaseModel.execute_query(
                """SELECT r.id, r.receipt_id, r.buyer_name, r.farmer_name,
                          r.grand_total, r.payment_type, r.created_at
                   FROM receipts r
                   ORDER BY r.created_at DESC LIMIT 20""",
                fetch_all=True
            ) or []
            for r in receipts:
                r = serialize_row(r)
                activities.append({
                    'type': 'purchase',
                    'message': f"{r.get('buyer_name', 'A buyer')} purchased from {r.get('farmer_name', 'a farmer')} - ₹{r.get('grand_total', 0)}",
                    'timestamp': r.get('created_at', ''),
                    'details': r
                })
        except Exception as e:
            print(f"Activity feed - receipts error: {e}")

        # 3. Recent orders
        try:
            orders = BaseModel.execute_query(
                """SELECT o.id, o.status, o.total_amount, o.created_at
                   FROM orders o
                   ORDER BY o.created_at DESC LIMIT 20""",
                fetch_all=True
            ) or []
            for o in orders:
                o = serialize_row(o)
                activities.append({
                    'type': 'order',
                    'message': f"Order #{o.get('id', '')} placed - ₹{o.get('total_amount', 0)} ({o.get('status', 'pending')})",
                    'timestamp': o.get('created_at', ''),
                    'details': o
                })
        except Exception as e:
            print(f"Activity feed - orders error: {e}")

        # Sort all activities by timestamp descending, limit 50
        activities.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        activities = activities[:50]

        return jsonify({
            'success': True,
            'activities': activities,
            'total': len(activities)
        }), 200

    except Exception as e:
        print(f"Activity feed error: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/receipts', methods=['GET'])
@jwt_required()
def get_all_receipts():
    """Get all receipts with farmer and buyer info"""
    try:
        user_id = get_jwt_identity()
        admin = BaseModel.execute_query(
            "SELECT *, admin_id as id FROM admins WHERE admin_id = %s",
            (int(user_id),), fetch_one=True
        )
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403

        receipts = BaseModel.execute_query(
            """SELECT r.id, r.receipt_id, r.buyer_id, r.farmer_id,
                      r.subtotal, r.discount, r.tax_amount, r.grand_total,
                      r.payment_type, r.payment_status,
                      COALESCE(r.buyer_name, CONCAT(b.first_name, ' ', b.last_name)) as buyer_name,
                      r.buyer_phone, r.buyer_email,
                      COALESCE(r.farmer_name, CONCAT(f.first_name, ' ', f.last_name)) as farmer_name,
                      r.farmer_phone, r.farmer_email,
                      r.created_at,
                      ri.product_name, ri.quantity_kg, ri.price_per_kg, ri.item_total
               FROM receipts r
               LEFT JOIN receipt_items ri ON r.id = ri.receipt_id
               LEFT JOIN farmers f ON r.farmer_id = f.id
               LEFT JOIN buyers b ON r.buyer_id = b.id
               ORDER BY r.created_at DESC
               LIMIT 100""",
            fetch_all=True
        ) or []

        serialized = serialize_rows(receipts)

        return jsonify({
            'success': True,
            'receipts': serialized,
            'total': len(serialized)
        }), 200

    except Exception as e:
        print(f"Get receipts error: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/farmer-profiles', methods=['GET'])
@jwt_required()
def get_farmer_profiles():
    """Get all farmer profiles with product counts"""
    try:
        user_id = get_jwt_identity()
        admin = BaseModel.execute_query(
            "SELECT *, admin_id as id FROM admins WHERE admin_id = %s",
            (int(user_id),), fetch_one=True
        )
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403

        farmers = BaseModel.execute_query(
            """SELECT f.*,
                      (SELECT COUNT(*) FROM products WHERE farmer_id = f.id) as product_count
               FROM farmers f
               ORDER BY f.created_at DESC""",
            fetch_all=True
        ) or []

        serialized = serialize_rows(farmers)

        return jsonify({
            'success': True,
            'farmers': serialized,
            'total': len(serialized)
        }), 200

    except Exception as e:
        print(f"Get farmer profiles error: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/buyer-profiles', methods=['GET'])
@jwt_required()
def get_buyer_profiles():
    """Get all buyer profiles with purchase counts"""
    try:
        user_id = get_jwt_identity()
        admin = BaseModel.execute_query(
            "SELECT *, admin_id as id FROM admins WHERE admin_id = %s",
            (int(user_id),), fetch_one=True
        )
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403

        buyers = BaseModel.execute_query(
            """SELECT b.*,
                      (SELECT COUNT(*) FROM receipts WHERE buyer_name LIKE CONCAT('%%', b.first_name, '%%')) as purchase_count
               FROM buyers b
               ORDER BY b.created_at DESC""",
            fetch_all=True
        ) or []

        serialized = serialize_rows(buyers)

        return jsonify({
            'success': True,
            'buyers': serialized,
            'total': len(serialized)
        }), 200

    except Exception as e:
        print(f"Get buyer profiles error: {e}")
        return jsonify({'error': str(e)}), 500
