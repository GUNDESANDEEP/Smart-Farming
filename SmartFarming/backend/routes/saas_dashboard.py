"""
SaaS Management Dashboard Routes
Path: /api/admin/saas
Provides: Analytics, Top Products, Revenue Breakdown, Monthly Sales, Admin Profile
"""

from fastapi import APIRouter, Request, Query, Depends
from fastapi.responses import JSONResponse
from utils.jwt_utils import get_current_user
from datetime import datetime, timedelta
from decimal import Decimal

import sys
sys.path.append('..')
from models.models import BaseModel

saas_dashboard_router = APIRouter(prefix='/api/admin/saas', tags=['SaaSDashboard'])


async def serialize_row(row):
    """Convert Decimal and datetime fields to JSON-serializable types"""
    if not row:
        return row
    result = {}
    for k, v in row.items():
        if isinstance(v, Decimal):
            result[k] = float(v)
        elif isinstance(v, datetime):
            result[k] = v.isoformat()
        else:
            result[k] = v
    return result


# ====================================================================
# 1. ANALYTICS OVERVIEW
# ====================================================================
@saas_dashboard_router.get('/analytics')
async def saas_analytics(request: Request, user_id: str = Depends(get_current_user)):
    """
    Get SaaS analytics overview: revenue, users, orders, growth
    """
    try:
        admin_id = user_id  # from dependency injection
        admin = BaseModel.execute_query(
            "SELECT *, admin_id as id FROM admins WHERE admin_id = %s",
            (int(admin_id),), fetch_one=True
        )
        if not admin:
            return JSONResponse(status_code=403, content={'error': 'Admin access required'})

        days = int(request.query_params.get('days', 30))
        now = datetime.now()
        date_from = now - timedelta(days=days)
        prev_from = date_from - timedelta(days=days)

        # Current period stats
        current = BaseModel.execute_query("""
            SELECT 
                COUNT(*) as total_orders,
                COALESCE(SUM(total_amount), 0) as total_revenue,
                COALESCE(AVG(total_amount), 0) as avg_order_value
            FROM orders
            WHERE created_at >= %s
        """, (date_from,), fetch_one=True) or {}

        # Previous period for growth comparison
        previous = BaseModel.execute_query("""
            SELECT 
                COUNT(*) as total_orders,
                COALESCE(SUM(total_amount), 0) as total_revenue
            FROM orders
            WHERE created_at >= %s AND created_at < %s
        """, (prev_from, date_from), fetch_one=True) or {}

        # User counts
        farmers = BaseModel.execute_query(
            "SELECT COUNT(*) as cnt FROM farmers", fetch_one=True
        )
        buyers = BaseModel.execute_query(
            "SELECT COUNT(*) as cnt FROM buyers", fetch_one=True
        )
        products = BaseModel.execute_query(
            "SELECT COUNT(*) as cnt FROM products", fetch_one=True
        )
        pending = BaseModel.execute_query(
            "SELECT COUNT(*) as cnt FROM products WHERE status = 'pending'",
            fetch_one=True
        )
        approved = BaseModel.execute_query(
            "SELECT COUNT(*) as cnt FROM products WHERE status = 'approved'",
            fetch_one=True
        )

        # New users this period
        new_farmers = BaseModel.execute_query(
            "SELECT COUNT(*) as cnt FROM farmers WHERE created_at >= %s",
            (date_from,), fetch_one=True
        )
        new_buyers = BaseModel.execute_query(
            "SELECT COUNT(*) as cnt FROM buyers WHERE created_at >= %s",
            (date_from,), fetch_one=True
        )

        # Growth calculations
        cur_rev = float(current.get('total_revenue', 0) or 0)
        prev_rev = float(previous.get('total_revenue', 0) or 0)
        cur_ord = int(current.get('total_orders', 0) or 0)
        prev_ord = int(previous.get('total_orders', 0) or 0)

        revenue_growth = ((cur_rev - prev_rev) / prev_rev * 100) if prev_rev > 0 else 0
        order_growth = ((cur_ord - prev_ord) / prev_ord * 100) if prev_ord > 0 else 0

        return {
            'success': True,
            'analytics': {
                'period_days': days,
                'total_revenue': cur_rev,
                'total_orders': cur_ord,
                'avg_order_value': float(current.get('avg_order_value', 0) or 0),
                'revenue_growth': round(revenue_growth, 1),
                'order_growth': round(order_growth, 1),
                'total_farmers': farmers['cnt'] if farmers else 0,
                'total_buyers': buyers['cnt'] if buyers else 0,
                'total_products': products['cnt'] if products else 0,
                'pending_products': pending['cnt'] if pending else 0,
                'approved_products': approved['cnt'] if approved else 0,
                'new_farmers': new_farmers['cnt'] if new_farmers else 0,
                'new_buyers': new_buyers['cnt'] if new_buyers else 0,
            }
        }

    except Exception as e:
        print(f"SaaS analytics error: {e}")
        return JSONResponse(status_code=500, content={'success': False, 'error': str(e)})


# ====================================================================
# 2. TOP SELLING PRODUCTS
# ====================================================================
@saas_dashboard_router.get('/top-products')
async def saas_top_products(request: Request, user_id: str = Depends(get_current_user)):
    """
    Get top selling products by revenue and quantity
    """
    try:
        admin_id = user_id  # from dependency injection
        admin = BaseModel.execute_query(
            "SELECT *, admin_id as id FROM admins WHERE admin_id = %s",
            (int(admin_id),), fetch_one=True
        )
        if not admin:
            return JSONResponse(status_code=403, content={'error': 'Admin access required'})

        days = int(request.query_params.get('days', 30))
        limit = int(request.query_params.get('limit', 10))
        date_from = datetime.now() - timedelta(days=days)

        # Top products by order revenue
        top_products = BaseModel.execute_query("""
            SELECT 
                p.id as product_id,
                p.name,
                p.category,
                p.price,
                p.unit,
                p.quantity as stock_quantity,
                p.status,
                f.first_name as farmer_first_name,
                f.last_name as farmer_last_name,
                f.location as farmer_location,
                COALESCE(order_stats.total_revenue, 0) as total_revenue,
                COALESCE(order_stats.units_sold, 0) as units_sold,
                COALESCE(order_stats.order_count, 0) as order_count
            FROM products p
            LEFT JOIN farmers f ON p.farmer_id = f.id
            LEFT JOIN (
                SELECT 
                    product_id,
                    SUM(total_amount) as total_revenue,
                    SUM(quantity) as units_sold,
                    COUNT(*) as order_count
                FROM orders
                WHERE created_at >= %s
                GROUP BY product_id
            ) order_stats ON p.id = order_stats.product_id
            ORDER BY COALESCE(order_stats.total_revenue, 0) DESC, p.created_at DESC
            LIMIT %s
        """, (date_from, limit), fetch_all=True) or []

        serialized = [serialize_row(p) for p in top_products]

        return {
            'success': True,
            'products': serialized,
            'period_days': days
        }

    except Exception as e:
        print(f"SaaS top products error: {e}")
        return JSONResponse(status_code=500, content={'success': False, 'error': str(e)})


# ====================================================================
# 3. REVENUE BREAKDOWN
# ====================================================================
@saas_dashboard_router.get('/revenue-breakdown')
async def saas_revenue_breakdown(request: Request, user_id: str = Depends(get_current_user)):
    """
    Get revenue breakdown by category
    """
    try:
        admin_id = user_id  # from dependency injection
        admin = BaseModel.execute_query(
            "SELECT *, admin_id as id FROM admins WHERE admin_id = %s",
            (int(admin_id),), fetch_one=True
        )
        if not admin:
            return JSONResponse(status_code=403, content={'error': 'Admin access required'})

        days = int(request.query_params.get('days', 30))
        date_from = datetime.now() - timedelta(days=days)

        # Revenue by category
        by_category = BaseModel.execute_query("""
            SELECT 
                COALESCE(p.category, 'Others') as category,
                SUM(o.total_amount) as revenue,
                COUNT(o.id) as orders,
                SUM(o.quantity) as units_sold
            FROM orders o
            LEFT JOIN products p ON o.product_id = p.id
            WHERE o.created_at >= %s
            GROUP BY p.category
            ORDER BY revenue DESC
        """, (date_from,), fetch_all=True) or []

        total_revenue = sum(float(c.get('revenue', 0) or 0) for c in by_category)

        formatted = []
        colors = ['#22c55e', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6']
        for i, cat in enumerate(by_category):
            rev = float(cat.get('revenue', 0) or 0)
            formatted.append({
                'category': cat.get('category', 'Others'),
                'revenue': rev,
                'orders': int(cat.get('orders', 0) or 0),
                'units_sold': float(cat.get('units_sold', 0) or 0),
                'percentage': round((rev / total_revenue * 100), 1) if total_revenue > 0 else 0,
                'color': colors[i % len(colors)]
            })

        return {
            'success': True,
            'total_revenue': total_revenue,
            'breakdown': formatted,
            'period_days': days
        }

    except Exception as e:
        print(f"SaaS revenue breakdown error: {e}")
        return JSONResponse(status_code=500, content={'success': False, 'error': str(e)})


# ====================================================================
# 4. MONTHLY SALES
# ====================================================================
@saas_dashboard_router.get('/monthly-sales')
async def saas_monthly_sales(request: Request, user_id: str = Depends(get_current_user)):
    """
    Get monthly sales data for charts
    """
    try:
        admin_id = user_id  # from dependency injection
        admin = BaseModel.execute_query(
            "SELECT *, admin_id as id FROM admins WHERE admin_id = %s",
            (int(admin_id),), fetch_one=True
        )
        if not admin:
            return JSONResponse(status_code=403, content={'error': 'Admin access required'})

        months = int(request.query_params.get('months', 6))
        date_from = datetime.now() - timedelta(days=months * 30)

        monthly_data = BaseModel.execute_query("""
            SELECT 
                TO_CHAR(created_at, 'YYYY-MM') as month,
                TO_CHAR(created_at, 'Mon') as month_name,
                SUM(total_amount) as revenue,
                COUNT(*) as orders,
                COUNT(DISTINCT buyer_id) as unique_buyers
            FROM orders
            WHERE created_at >= %s
            GROUP BY TO_CHAR(created_at, 'YYYY-MM'), TO_CHAR(created_at, 'Mon')
            ORDER BY month ASC
        """, (date_from,), fetch_all=True) or []

        serialized = [serialize_row(m) for m in monthly_data]

        return {
            'success': True,
            'monthly_data': serialized,
            'months': months
        }

    except Exception as e:
        print(f"SaaS monthly sales error: {e}")
        return JSONResponse(status_code=500, content={'success': False, 'error': str(e)})


# ====================================================================
# 5. ADMIN PROFILE
# ====================================================================
@saas_dashboard_router.get('/profile')
async def saas_admin_profile(request: Request, user_id: str = Depends(get_current_user)):
    """
    Get admin profile information
    """
    try:
        admin_id = user_id  # from dependency injection
        admin = BaseModel.execute_query(
            "SELECT * FROM admins WHERE admin_id = %s",
            (int(admin_id),), fetch_one=True
        )
        if not admin:
            return JSONResponse(status_code=403, content={'error': 'Admin access required'})

        # Get admin activity stats
        total_approvals = BaseModel.execute_query("""
            SELECT COUNT(*) as cnt FROM admin_activity_log
            WHERE admin_id = %s AND action = 'approve_product'
        """, (int(admin_id),), fetch_one=True)

        total_rejections = BaseModel.execute_query("""
            SELECT COUNT(*) as cnt FROM admin_activity_log
            WHERE admin_id = %s AND action = 'reject_product'
        """, (int(admin_id),), fetch_one=True)

        total_actions = BaseModel.execute_query("""
            SELECT COUNT(*) as cnt FROM admin_activity_log
            WHERE admin_id = %s
        """, (int(admin_id),), fetch_one=True)

        profile = serialize_row(admin)
        profile['total_approvals'] = total_approvals['cnt'] if total_approvals else 0
        profile['total_rejections'] = total_rejections['cnt'] if total_rejections else 0
        profile['total_actions'] = total_actions['cnt'] if total_actions else 0

        return {
            'success': True,
            'profile': profile
        }

    except Exception as e:
        print(f"SaaS admin profile error: {e}")
        return JSONResponse(status_code=500, content={'success': False, 'error': str(e)})
