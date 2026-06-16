"""
Admin Analytics Routes
Handles: Sales reports, top products/farmers, user analytics, revenue breakdown
Path: /api/admin/analytics
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from dateutil import rrule, parser

import sys
sys.path.append('..')
from models.models import Admin, Order, Product, Farmer

admin_analytics_bp = Blueprint('admin_analytics', __name__, url_prefix='/api/admin/analytics')

# ====================================================================
# 1. ANALYTICS DASHBOARD
# ====================================================================
@admin_analytics_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_analytics_dashboard():
    """
    Get comprehensive analytics dashboard
    
    Response:
    {
        "success": true,
        "analytics": {
            "period": "Last 30 days",
            "total_revenue": 3200000,
            "total_orders": 234,
            "total_customers": 1890,
            "average_order_value": 13675,
            "revenue_growth": 15.3,
            "order_growth": 8.5,
            "charts": {
                "daily_sales": [...],
                "category_breakdown": [...]
            }
        }
    }
    """
    try:
        days = request.args.get('days', type=int, default=30)
        date_from = datetime.now() - timedelta(days=days)
        date_to = datetime.now()
        
        order_obj = Order()
        
        # Get revenue
        total_revenue = order_obj.get_revenue_by_date_range(date_from, date_to)
        total_orders = order_obj.count_orders_by_date_range(date_from, date_to)
        
        # Get previous period for comparison
        previous_from = date_from - timedelta(days=days)
        previous_to = date_from
        prev_revenue = order_obj.get_revenue_by_date_range(previous_from, previous_to)
        prev_orders = order_obj.count_orders_by_date_range(previous_from, previous_to)
        
        # Calculate growth
        revenue_growth = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
        order_growth = ((total_orders - prev_orders) / prev_orders * 100) if prev_orders > 0 else 0
        
        # Get unique customers
        unique_customers = order_obj.count_unique_buyers_by_date_range(date_from, date_to)
        
        # Average order value
        avg_order_value = (total_revenue / total_orders) if total_orders > 0 else 0
        
        # Daily sales data
        daily_sales = order_obj.get_daily_revenue(date_from, date_to)
        
        # Category breakdown
        category_sales = order_obj.get_revenue_by_category(date_from, date_to)
        
        return jsonify({
            'success': True,
            'analytics': {
                'period': f'Last {days} days',
                'total_revenue': float(total_revenue or 0),
                'total_orders': total_orders,
                'total_customers': unique_customers,
                'average_order_value': float(avg_order_value),
                'revenue_growth': round(revenue_growth, 2),
                'order_growth': round(order_growth, 2),
                'charts': {
                    'daily_sales': daily_sales,
                    'category_breakdown': category_sales
                }
            }
        }), 200
        
    except Exception as e:
        print(f"Error in get_analytics_dashboard: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch analytics'}), 500


# ====================================================================
# 2. MONTHLY SALES REPORT
# ====================================================================
@admin_analytics_bp.route('/sales/monthly', methods=['GET'])
@jwt_required()
def get_monthly_sales():
    """
    Get monthly sales report with trends
    
    Query Parameters:
    - months: Number of months to fetch (default: 12)
    
    Response:
    {
        "success": true,
        "report": {
            "title": "Monthly Sales Report",
            "data": [
                {
                    "month": "2025-05",
                    "revenue": 2500000,
                    "orders": 145,
                    "customers": 890,
                    "growth": 8.5
                }
            ],
            "totals": {...}
        }
    }
    """
    try:
        months = request.args.get('months', type=int, default=12)
        
        order_obj = Order()
        monthly_data = order_obj.get_monthly_revenue(months=months)
        
        formatted_data = []
        total_revenue = 0
        total_orders = 0
        total_customers = 0
        
        prev_revenue = 0
        for data in monthly_data:
            growth = 0
            if prev_revenue > 0:
                growth = ((data['revenue'] - prev_revenue) / prev_revenue * 100)
            
            formatted_data.append({
                'month': data['month'].strftime('%Y-%m'),
                'revenue': float(data['revenue'] or 0),
                'orders': data['order_count'],
                'customers': data.get('unique_customers', 0),
                'growth': round(growth, 2)
            })
            
            total_revenue += data['revenue'] or 0
            total_orders += data['order_count']
            total_customers += data.get('unique_customers', 0)
            prev_revenue = data['revenue'] or 0
        
        return jsonify({
            'success': True,
            'report': {
                'title': 'Monthly Sales Report',
                'data': formatted_data,
                'totals': {
                    'total_revenue': float(total_revenue),
                    'total_orders': total_orders,
                    'total_customers': total_customers,
                    'average_monthly_revenue': float(total_revenue / len(formatted_data)) if formatted_data else 0
                }
            }
        }), 200
        
    except Exception as e:
        print(f"Error in get_monthly_sales: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch monthly sales'}), 500


# ====================================================================
# 3. TOP SELLING PRODUCTS
# ====================================================================
@admin_analytics_bp.route('/products/top-selling', methods=['GET'])
@jwt_required()
def get_top_products():
    """
    Get top selling products by quantity and revenue
    
    Query Parameters:
    - limit: Number of top products (default: 10)
    - days: Period to analyze (default: 30)
    
    Response:
    {
        "success": true,
        "products": [
            {
                "product_id": 45,
                "name": "Organic Tomatoes",
                "category": "Vegetables",
                "units_sold": 345,
                "revenue": 15800,
                "rating": 4.5
            }
        ]
    }
    """
    try:
        limit = request.args.get('limit', type=int, default=10)
        days = request.args.get('days', type=int, default=30)
        
        date_from = datetime.now() - timedelta(days=days)
        date_to = datetime.now()
        
        order_obj = Order()
        top_products = order_obj.get_top_products(date_from, date_to, limit=limit)
        
        formatted_products = []
        for product in top_products:
            formatted_products.append({
                'product_id': product['product_id'],
                'name': product['product_name'],
                'category': product.get('category', ''),
                'units_sold': product['quantity_sold'],
                'revenue': float(product.get('revenue', 0)),
                'rating': float(product.get('rating', 0))
            })
        
        return jsonify({
            'success': True,
            'products': formatted_products
        }), 200
        
    except Exception as e:
        print(f"Error in get_top_products: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch top products'}), 500


# ====================================================================
# 4. TOP FARMERS
# ====================================================================
@admin_analytics_bp.route('/farmers/top', methods=['GET'])
@jwt_required()
def get_top_farmers():
    """
    Get top farmers by sales and ratings
    
    Query Parameters:
    - limit: Number of top farmers (default: 10)
    - days: Period to analyze (default: 30)
    
    Response:
    {
        "success": true,
        "farmers": [
            {
                "farmer_id": 12,
                "name": "Ravi Kumar",
                "total_sales": 450000,
                "orders_fulfilled": 45,
                "rating": 4.8,
                "reviews": 89
            }
        ]
    }
    """
    try:
        limit = request.args.get('limit', type=int, default=10)
        days = request.args.get('days', type=int, default=30)
        
        date_from = datetime.now() - timedelta(days=days)
        date_to = datetime.now()
        
        farmer_obj = Farmer()
        top_farmers = farmer_obj.get_top_farmers(date_from, date_to, limit=limit)
        
        formatted_farmers = []
        for farmer in top_farmers:
            formatted_farmers.append({
                'farmer_id': farmer['farmer_id'],
                'name': farmer['name'],
                'total_sales': float(farmer.get('total_sales', 0)),
                'orders_fulfilled': farmer.get('order_count', 0),
                'rating': float(farmer.get('rating', 0)),
                'reviews': farmer.get('review_count', 0)
            })
        
        return jsonify({
            'success': True,
            'farmers': formatted_farmers
        }), 200
        
    except Exception as e:
        print(f"Error in get_top_farmers: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch top farmers'}), 500


# ====================================================================
# 5. ACTIVE USERS ANALYTICS
# ====================================================================
@admin_analytics_bp.route('/users/active', methods=['GET'])
@jwt_required()
def get_active_users():
    """
    Get active users statistics (daily/weekly/monthly)
    
    Response:
    {
        "success": true,
        "active_users": {
            "today": 1234,
            "this_week": 5678,
            "this_month": 12450,
            "farmers_active": {
                "today": 234,
                "this_week": 890,
                "this_month": 1250
            },
            "buyers_active": {
                "today": 1000,
                "this_week": 4788,
                "this_month": 11200
            }
        }
    }
    """
    try:
        order_obj = Order()
        farmer_obj = Farmer()
        
        # Today
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_orders = order_obj.count_orders_by_date_range(today_start, datetime.now())
        today_active = order_obj.count_unique_buyers_by_date_range(today_start, datetime.now())
        today_farmers = farmer_obj.count_active_by_date_range(today_start, datetime.now())
        
        # This week
        week_start = datetime.now() - timedelta(days=7)
        week_active = order_obj.count_unique_buyers_by_date_range(week_start, datetime.now())
        week_farmers = farmer_obj.count_active_by_date_range(week_start, datetime.now())
        
        # This month
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_active = order_obj.count_unique_buyers_by_date_range(month_start, datetime.now())
        month_farmers = farmer_obj.count_active_by_date_range(month_start, datetime.now())
        
        return jsonify({
            'success': True,
            'active_users': {
                'today': today_active,
                'this_week': week_active,
                'this_month': month_active,
                'farmers_active': {
                    'today': today_farmers,
                    'this_week': week_farmers,
                    'this_month': month_farmers
                },
                'buyers_active': {
                    'today': today_active,
                    'this_week': week_active,
                    'this_month': month_active
                }
            }
        }), 200
        
    except Exception as e:
        print(f"Error in get_active_users: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch active users'}), 500


# ====================================================================
# 6. REVENUE BREAKDOWN
# ====================================================================
@admin_analytics_bp.route('/revenue/breakdown', methods=['GET'])
@jwt_required()
def get_revenue_breakdown():
    """
    Get revenue breakdown by category and payment method
    
    Query Parameters:
    - days: Period to analyze (default: 30)
    
    Response:
    {
        "success": true,
        "breakdown": {
            "by_category": [
                {
                    "category": "Vegetables",
                    "revenue": 1200000,
                    "percentage": 37.5
                }
            ],
            "by_payment_method": [
                {
                    "method": "UPI",
                    "revenue": 1500000,
                    "percentage": 46.9
                }
            ]
        }
    }
    """
    try:
        days = request.args.get('days', type=int, default=30)
        date_from = datetime.now() - timedelta(days=days)
        date_to = datetime.now()
        
        order_obj = Order()
        
        # Revenue by category
        category_revenue = order_obj.get_revenue_by_category(date_from, date_to)
        total_revenue = sum([c.get('revenue', 0) for c in category_revenue])
        
        formatted_categories = []
        for cat in category_revenue:
            percentage = (cat.get('revenue', 0) / total_revenue * 100) if total_revenue > 0 else 0
            formatted_categories.append({
                'category': cat.get('category', 'Unknown'),
                'revenue': float(cat.get('revenue', 0)),
                'percentage': round(percentage, 2)
            })
        
        # Revenue by payment method
        payment_revenue = order_obj.get_revenue_by_payment_method(date_from, date_to)
        
        formatted_payments = []
        for payment in payment_revenue:
            percentage = (payment.get('revenue', 0) / total_revenue * 100) if total_revenue > 0 else 0
            method_names = {
                'razorpay': 'Razorpay (Card/UPI)',
                'cod': 'Cash on Delivery',
                'upi': 'UPI',
                'card': 'Card'
            }
            formatted_payments.append({
                'method': method_names.get(payment.get('payment_method', ''), payment.get('payment_method', 'Unknown')),
                'revenue': float(payment.get('revenue', 0)),
                'percentage': round(percentage, 2)
            })
        
        return jsonify({
            'success': True,
            'breakdown': {
                'total_revenue': float(total_revenue),
                'by_category': formatted_categories,
                'by_payment_method': formatted_payments
            }
        }), 200
        
    except Exception as e:
        print(f"Error in get_revenue_breakdown: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch revenue breakdown'}), 500


# ====================================================================
# 7. SALES TRENDS
# ====================================================================
@admin_analytics_bp.route('/trends', methods=['GET'])
@jwt_required()
def get_sales_trends():
    """
    Get sales trends and forecasts
    
    Query Parameters:
    - days: Period to analyze (default: 90)
    
    Response:
    {
        "success": true,
        "trends": {
            "daily_data": [...],
            "weekly_avg": [...],
            "trend_direction": "upward",
            "forecast": [...]
        }
    }
    """
    try:
        days = request.args.get('days', type=int, default=90)
        date_from = datetime.now() - timedelta(days=days)
        date_to = datetime.now()
        
        order_obj = Order()
        
        # Daily sales data
        daily_data = order_obj.get_daily_revenue(date_from, date_to)
        
        # Calculate weekly average
        weekly_avg = []
        for i in range(0, len(daily_data), 7):
            week_data = daily_data[i:i+7]
            if week_data:
                avg_revenue = sum([d.get('revenue', 0) for d in week_data]) / len(week_data)
                weekly_avg.append({
                    'week': week_data[0].get('date'),
                    'average_revenue': float(avg_revenue)
                })
        
        # Determine trend
        if len(daily_data) >= 2:
            recent_avg = sum([d.get('revenue', 0) for d in daily_data[-7:]]) / 7
            older_avg = sum([d.get('revenue', 0) for d in daily_data[:7]]) / 7
            trend_direction = 'upward' if recent_avg > older_avg else 'downward'
        else:
            trend_direction = 'stable'
        
        return jsonify({
            'success': True,
            'trends': {
                'daily_data': daily_data,
                'weekly_avg': weekly_avg,
                'trend_direction': trend_direction,
                'days_analyzed': days
            }
        }), 200
        
    except Exception as e:
        print(f"Error in get_sales_trends: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch sales trends'}), 500


# ====================================================================
# 8. CUSTOM REPORT GENERATION
# ====================================================================
@admin_analytics_bp.route('/generate-report', methods=['POST'])
@jwt_required()
def generate_custom_report():
    """
    Generate custom analytics report
    
    Request:
    {
        "report_type": "sales_summary",
        "date_from": "2026-05-01",
        "date_to": "2026-05-31",
        "include_categories": true,
        "include_payments": true
    }
    
    Response:
    {
        "success": true,
        "report_id": 1,
        "report_url": "..."
    }
    """
    try:
        admin_id = get_jwt_identity()
        data = request.get_json()
        
        report_type = data.get('report_type', 'sales_summary')
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        
        # Parse dates
        try:
            date_from = parser.parse(date_from).date() if date_from else (datetime.now() - timedelta(days=30)).date()
            date_to = parser.parse(date_to).date() if date_to else datetime.now().date()
        except:
            return jsonify({'success': False, 'error': 'Invalid date format'}), 400
        
        # Prepare report data
        order_obj = Order()
        report_data = {
            'type': report_type,
            'total_revenue': float(order_obj.get_revenue_by_date_range(date_from, date_to) or 0),
            'total_orders': order_obj.count_orders_by_date_range(date_from, date_to),
            'date_from': date_from.isoformat(),
            'date_to': date_to.isoformat()
        }
        
        # Save report
        admin = Admin()
        report_id = admin.save_analytics_report(
            report_type=report_type,
            period_start=date_from,
            period_end=date_to,
            data=report_data,
            generated_by=admin_id
        )
        
        if not report_id:
            return jsonify({'success': False, 'error': 'Failed to generate report'}), 500
        
        return jsonify({
            'success': True,
            'report_id': report_id,
            'report': report_data,
            'message': 'Report generated successfully'
        }), 201
        
    except Exception as e:
        print(f"Error in generate_custom_report: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to generate report'}), 500
