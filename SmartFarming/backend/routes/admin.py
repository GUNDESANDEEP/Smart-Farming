"""
Admin Module - User Management, Product Approval, Analytics
Flask Blueprint (compatible with app.py)
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.models import (
    User, Farmer, Buyer, Admin, Product, Order, Payment, Review, Notification,
    BaseModel
)
from datetime import datetime, timedelta
from decimal import Decimal
import json

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# ============================================================================
# HELPER - Verify admin & serialize
# ============================================================================

def _check_admin():
    """Check if current user is admin. Returns admin dict or None."""
    try:
        user_id = get_jwt_identity()
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

@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard():
    """Get admin dashboard statistics"""
    try:
        admin = _check_admin()
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403

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

        return jsonify({
            'success': True,
            'total_users': stats['total_farmers'] + stats['total_buyers'],
            'total_orders': stats['total_orders'],
            'total_revenue': stats['total_revenue'],
            'pending_products': stats['pending_products'],
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
    """Get list of all users (farmers + buyers)"""
    try:
        admin = _check_admin()
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403

        farmers = BaseModel.execute_query(
            "SELECT id, first_name, last_name, email, phone, location, is_active, created_at FROM farmers ORDER BY created_at DESC",
            fetch_all=True
        ) or []

        buyers = BaseModel.execute_query(
            "SELECT id, first_name, last_name, email, phone, location, is_verified, created_at FROM buyers ORDER BY created_at DESC",
            fetch_all=True
        ) or []

        return jsonify({
            'success': True,
            'farmers': _serialize(farmers),
            'buyers': _serialize(buyers),
            'total_farmers': len(farmers),
            'total_buyers': len(buyers)
        }), 200

    except Exception as e:
        print(f"Get users error: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/users/<target_user_id>', methods=['GET'])
@jwt_required()
def get_user_details(target_user_id):
    """Get specific user details"""
    try:
        admin = _check_admin()
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403

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
            return jsonify({'error': 'User not found'}), 404

        return jsonify({'user': _serialize_one(user)}), 200

    except Exception as e:
        print(f"Get user details error: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/users/<target_user_id>/suspend', methods=['POST'])
@jwt_required()
def suspend_user(target_user_id):
    """Suspend user account"""
    try:
        admin = _check_admin()
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403

        data = request.get_json(silent=True) or {}
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
            return jsonify({'error': 'User not found'}), 404

        # Log action
        try:
            admin_id = get_jwt_identity()
            BaseModel.execute_insert(
                """INSERT INTO admin_activity_log (admin_id, action, module, target_id)
                   VALUES (%s, %s, %s, %s)""",
                (int(admin_id), 'suspend_user', role, str(target_user_id))
            )
        except Exception:
            pass

        return jsonify({'message': 'User suspended successfully'}), 200

    except Exception as e:
        print(f"Suspend user error: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/users/<target_user_id>/activate', methods=['POST'])
@jwt_required()
def activate_user(target_user_id):
    """Activate suspended user"""
    try:
        admin = _check_admin()
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403

        data = request.get_json(silent=True) or {}
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
            return jsonify({'error': 'User not found'}), 404

        # Log action
        try:
            admin_id = get_jwt_identity()
            BaseModel.execute_insert(
                """INSERT INTO admin_activity_log (admin_id, action, module, target_id)
                   VALUES (%s, %s, %s, %s)""",
                (int(admin_id), 'activate_user', role, str(target_user_id))
            )
        except Exception:
            pass

        return jsonify({'message': 'User activated successfully'}), 200

    except Exception as e:
        print(f"Activate user error: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/users/<target_user_id>/delete', methods=['POST'])
@jwt_required()
def delete_user(target_user_id):
    """Permanently delete user from database"""
    try:
        admin = _check_admin()
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403

        data = request.get_json(silent=True) or {}
        role = data.get('role', '')

        deleted = False

        if role == 'farmer' or not role:
            result = BaseModel.execute_query(
                "SELECT id, first_name, last_name, email FROM farmers WHERE id = %s",
                (target_user_id,), fetch_one=True
            )
            if result:
                # Delete farmer's products (foreign key)
                try:
                    BaseModel.execute_query("DELETE FROM products WHERE farmer_id = %s", (target_user_id,))
                except Exception:
                    pass
                # Delete farmer's orders
                try:
                    BaseModel.execute_query("DELETE FROM orders WHERE farmer_id = %s", (target_user_id,))
                except Exception:
                    pass
                # Delete farmer's wallet
                try:
                    BaseModel.execute_query("DELETE FROM wallet WHERE farmer_id = %s", (target_user_id,))
                except Exception:
                    pass
                # Delete the farmer
                BaseModel.execute_query("DELETE FROM farmers WHERE id = %s", (target_user_id,))
                deleted = True
                role = 'farmer'

        if not deleted and (role == 'buyer' or not role):
            result = BaseModel.execute_query(
                "SELECT id, first_name, last_name, email FROM buyers WHERE id = %s",
                (target_user_id,), fetch_one=True
            )
            if result:
                # Delete buyer's orders
                try:
                    BaseModel.execute_query("DELETE FROM orders WHERE buyer_id = %s", (target_user_id,))
                except Exception:
                    pass
                # Delete buyer's cart items
                try:
                    BaseModel.execute_query("DELETE FROM cart WHERE buyer_id = %s", (target_user_id,))
                except Exception:
                    pass
                # Delete the buyer
                BaseModel.execute_query("DELETE FROM buyers WHERE id = %s", (target_user_id,))
                deleted = True
                role = 'buyer'

        if not deleted:
            return jsonify({'error': 'User not found'}), 404

        # Log action
        try:
            admin_id = get_jwt_identity()
            BaseModel.execute_insert(
                """INSERT INTO admin_activity_log (admin_id, action, module, target_id)
                   VALUES (%s, %s, %s, %s)""",
                (int(admin_id), 'delete_user', role, str(target_user_id))
            )
        except Exception:
            pass

        return jsonify({'message': 'User permanently deleted'}), 200

    except Exception as e:
        print(f"Delete user error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# FARMER VERIFICATION
# ============================================================================

@admin_bp.route('/farmers/pending-verification', methods=['GET'])
@jwt_required()
def get_pending_farmers():
    """Get farmers pending verification"""
    try:
        admin = _check_admin()
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403

        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        offset = (page - 1) * limit

        farmers = BaseModel.execute_query(
            """SELECT f.* FROM farmers f
               WHERE f.is_verified = FALSE
               ORDER BY f.created_at ASC LIMIT %s OFFSET %s""",
            (limit, offset), fetch_all=True
        ) or []

        return jsonify({'farmers': _serialize(farmers), 'page': page, 'limit': limit}), 200

    except Exception as e:
        print(f"Get pending farmers error: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/farmers/<int:farmer_id>/verify', methods=['POST'])
@jwt_required()
def verify_farmer(farmer_id):
    """Verify farmer"""
    try:
        admin = _check_admin()
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403

        farmer = Farmer.get_by_id(farmer_id)
        if not farmer:
            return jsonify({'error': 'Farmer not found'}), 404

        Farmer.update(farmer_id, is_verified=True)
        return jsonify({'message': 'Farmer verified successfully'}), 200

    except Exception as e:
        print(f"Verify farmer error: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/farmers/<int:farmer_id>/reject', methods=['POST'])
@jwt_required()
def reject_farmer(farmer_id):
    """Reject farmer verification"""
    try:
        admin = _check_admin()
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403

        farmer = Farmer.get_by_id(farmer_id)
        if not farmer:
            return jsonify({'error': 'Farmer not found'}), 404

        data = request.get_json(silent=True) or {}
        reason = data.get('reason', 'Verification rejected')

        BaseModel.execute_query(
            "UPDATE farmers SET is_verified = FALSE WHERE id = %s", (farmer_id,)
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
            query += " WHERE p.status = %s"
            params.append(status_filter)
        query += " ORDER BY p.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        products = BaseModel.execute_query(query, tuple(params), fetch_all=True) or []

        return jsonify({'products': _serialize(products), 'total': len(products)}), 200

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

        products = BaseModel.execute_query(
            """SELECT p.*, f.first_name, f.last_name, f.phone as farmer_phone
               FROM products p
               LEFT JOIN farmers f ON p.farmer_id = f.id
               WHERE p.status = 'pending'
               ORDER BY p.created_at ASC LIMIT %s OFFSET %s""",
            (limit, offset), fetch_all=True
        ) or []

        return jsonify({'products': _serialize(products), 'page': page, 'limit': limit}), 200

    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/products/<int:product_id>/approve', methods=['POST'])
@jwt_required()
def approve_product(product_id):
    """Approve product"""
    try:
        product = BaseModel.execute_query(
            "SELECT id, name FROM products WHERE id = %s", (product_id,), fetch_one=True
        )
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        BaseModel.execute_query("UPDATE products SET status = 'approved' WHERE id = %s", (product_id,))
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
            "SELECT id, name FROM products WHERE id = %s", (product_id,), fetch_one=True
        )
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        BaseModel.execute_query("UPDATE products SET status = 'rejected' WHERE id = %s", (product_id,))
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
        admin = _check_admin()
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403

        days = request.args.get('days', 30, type=int)
        start_date = datetime.now() - timedelta(days=days)

        analytics = BaseModel.execute_query(
            """SELECT DATE(o.created_at) as date, SUM(o.total_amount) as daily_revenue, COUNT(*) as order_count
               FROM orders o
               WHERE o.created_at >= %s AND o.status = 'delivered'
               GROUP BY DATE(o.created_at)
               ORDER BY date DESC""",
            (start_date,), fetch_all=True
        ) or []

        return jsonify({'period_days': days, 'analytics': _serialize(analytics)}), 200

    except Exception as e:
        print(f"Analytics revenue error: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/analytics/orders', methods=['GET'])
@jwt_required()
def analytics_orders():
    """Get orders analytics"""
    try:
        admin = _check_admin()
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403

        days = request.args.get('days', 30, type=int)
        start_date = datetime.now() - timedelta(days=days)

        analytics = BaseModel.execute_query(
            """SELECT status, COUNT(*) as count,
                      AVG(total_amount) as avg_price, SUM(total_amount) as total_price
               FROM orders WHERE created_at >= %s GROUP BY status""",
            (start_date,), fetch_all=True
        ) or []

        return jsonify({'period_days': days, 'analytics': _serialize(analytics)}), 200

    except Exception as e:
        print(f"Analytics orders error: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/analytics/users', methods=['GET'])
@jwt_required()
def analytics_users():
    """Get users growth analytics"""
    try:
        admin = _check_admin()
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403

        days = request.args.get('days', 30, type=int)
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

        return jsonify({'period_days': days, 'analytics': analytics}), 200

    except Exception as e:
        print(f"Analytics users error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# DISPUTES
# ============================================================================

@admin_bp.route('/disputes', methods=['GET'])
@jwt_required()
def get_disputes():
    """Get disputes/complaints"""
    try:
        admin = _check_admin()
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403

        status = request.args.get('status', 'open')
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        offset = (page - 1) * limit

        try:
            disputes = BaseModel.execute_query(
                "SELECT * FROM disputes WHERE status = %s ORDER BY created_at DESC LIMIT %s OFFSET %s",
                (status, limit, offset), fetch_all=True
            ) or []
        except Exception:
            disputes = []

        return jsonify({'disputes': _serialize(disputes), 'page': page, 'limit': limit}), 200

    except Exception as e:
        print(f"Get disputes error: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/disputes/<int:dispute_id>/resolve', methods=['POST'])
@jwt_required()
def resolve_dispute(dispute_id):
    """Resolve dispute"""
    try:
        admin = _check_admin()
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403

        data = request.get_json(silent=True) or {}
        resolution = data.get('resolution', '')

        try:
            BaseModel.execute_query(
                "UPDATE disputes SET status = %s, resolution = %s WHERE id = %s",
                ('resolved', resolution, dispute_id)
            )
        except Exception:
            pass

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
        admin = _check_admin()
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403

        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 50, type=int)
        offset = (page - 1) * limit

        try:
            logs = BaseModel.execute_query(
                "SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT %s OFFSET %s",
                (limit, offset), fetch_all=True
            ) or []
        except Exception:
            logs = []

        return jsonify({'logs': _serialize(logs), 'page': page, 'limit': limit}), 200

    except Exception as e:
        print(f"Get audit logs error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# ACTIVITY FEED
# ============================================================================

@admin_bp.route('/activity-feed', methods=['GET'])
@jwt_required()
def get_activity_feed():
    """Get recent platform activity"""
    try:
        admin = _check_admin()
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403

        limit = request.args.get('limit', 20, type=int)
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

        return jsonify({'activities': activities[:limit]}), 200

    except Exception as e:
        print(f"Activity feed error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# RECEIPTS
# ============================================================================

@admin_bp.route('/receipts', methods=['GET'])
@jwt_required()
def get_all_receipts():
    """Get all payment receipts"""
    try:
        admin = _check_admin()
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403

        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 50, type=int)
        offset = (page - 1) * limit

        try:
            receipts = BaseModel.execute_query(
                """SELECT p.*, o.order_number, o.status as order_status
                   FROM payments p
                   LEFT JOIN orders o ON p.order_id = o.id
                   ORDER BY p.created_at DESC LIMIT %s OFFSET %s""",
                (limit, offset), fetch_all=True
            ) or []
        except Exception:
            receipts = []

        return jsonify({'receipts': _serialize(receipts), 'total': len(receipts)}), 200

    except Exception as e:
        print(f"Get receipts error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# FARMER / BUYER PROFILES (Admin view)
# ============================================================================

@admin_bp.route('/farmer-profiles', methods=['GET'])
@jwt_required()
def get_farmer_profiles():
    """Get all farmer profiles for admin"""
    try:
        admin = _check_admin()
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403

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

        return jsonify({'farmers': _serialize(farmers)}), 200

    except Exception as e:
        print(f"Get farmer profiles error: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/buyer-profiles', methods=['GET'])
@jwt_required()
def get_buyer_profiles():
    """Get all buyer profiles for admin"""
    try:
        admin = _check_admin()
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403

        buyers = BaseModel.execute_query(
            """SELECT b.*, COUNT(DISTINCT o.id) as order_count,
                      COALESCE(SUM(o.total_amount), 0) as total_spent
               FROM buyers b
               LEFT JOIN orders o ON b.id = o.buyer_id
               GROUP BY b.id
               ORDER BY b.created_at DESC""",
            fetch_all=True
        ) or []

        return jsonify({'buyers': _serialize(buyers)}), 200

    except Exception as e:
        print(f"Get buyer profiles error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# PLATFORM EARNINGS
# ============================================================================

@admin_bp.route('/platform-earnings', methods=['GET'])
@jwt_required()
def get_platform_earnings():
    """Get platform earnings breakdown"""
    try:
        admin = _check_admin()
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403

        try:
            earnings = BaseModel.execute_query(
                "SELECT * FROM platform_earnings ORDER BY created_at DESC LIMIT 50",
                fetch_all=True
            ) or []
        except Exception:
            earnings = []

        return jsonify({'earnings': _serialize(earnings)}), 200

    except Exception as e:
        print(f"Get platform earnings error: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/platform-earnings/<int:earning_id>/settle', methods=['POST'])
@jwt_required()
def settle_earning(earning_id):
    """Mark earning as settled"""
    try:
        admin = _check_admin()
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403

        try:
            BaseModel.execute_query(
                "UPDATE platform_earnings SET settlement_status = 'settled', settled_at = NOW() WHERE id = %s",
                (earning_id,)
            )
        except Exception:
            pass

        return jsonify({'success': True, 'message': 'Marked as settled'}), 200

    except Exception as e:
        print(f"Settle earning error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# SaaS ANALYTICS (frontend expects these)
# ============================================================================

@admin_bp.route('/saas/analytics', methods=['GET'])
@jwt_required()
def saas_analytics():
    """SaaS analytics overview"""
    try:
        return jsonify({'revenue': 0, 'orders': 0, 'users': 0, 'products': 0}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/saas/top-products', methods=['GET'])
@jwt_required()
def saas_top_products():
    """Top products"""
    return jsonify([]), 200

@admin_bp.route('/saas/revenue-breakdown', methods=['GET'])
@jwt_required()
def saas_revenue_breakdown():
    """Revenue breakdown"""
    return jsonify([]), 200

@admin_bp.route('/saas/monthly-sales', methods=['GET'])
@jwt_required()
def saas_monthly_sales():
    """Monthly sales"""
    return jsonify([]), 200

@admin_bp.route('/saas/profile', methods=['GET'])
@jwt_required()
def saas_profile():
    """Admin profile"""
    try:
        user_id = get_jwt_identity()
        admin = _check_admin()
        return jsonify(admin or {'id': user_id, 'role': 'admin'}), 200
    except Exception:
        return jsonify({}), 200
