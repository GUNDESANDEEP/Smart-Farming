from flask import Blueprint, request, jsonify
from functools import wraps
from datetime import datetime
import mysql.connector
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import requests
from typing import Optional, Dict, List
import logging

admin_advanced_features_bp = Blueprint('admin_advanced_features', __name__, url_prefix='/api/admin/advanced-features')
logger = logging.getLogger(__name__)

# Email Configuration
EMAIL_CONFIG = {
    'smtp_server': os.getenv('SMTP_HOST', os.getenv('SMTP_SERVER', 'smtp.gmail.com')),
    'smtp_port': int(os.getenv('SMTP_PORT', 587)),
    'sender_email': os.getenv('EMAIL_SENDER', 'noreply@smartfarming.com'),
    'sender_password': os.getenv('EMAIL_PASSWORD', ''),
}

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'smart_farming')
    )

# ==================== EMAIL NOTIFICATION SERVICE ====================

def send_email(recipient_email: str, subject: str, body: str, html: Optional[str] = None) -> bool:
    """
    Send email notification to recipient - SMTP authentication is MANDATORY
    
    Args:
        recipient_email: Email address
        subject: Email subject
        body: Plain text body
        html: HTML template (optional)
    
    Returns:
        bool: Success/failure
    
    Raises:
        RuntimeError: If SMTP credentials are not configured or authentication fails
    """
    # Pre-check: SMTP credentials MUST be configured
    if not EMAIL_CONFIG['sender_email'] or not EMAIL_CONFIG['sender_password']:
        raise RuntimeError(
            "SMTP Authentication FAILED: EMAIL_SENDER and EMAIL_PASSWORD must be set in .env. "
            "Email sending is mandatory and cannot be skipped."
        )
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = recipient_email

        # Attach plain text
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach HTML if provided
        if html:
            msg.attach(MIMEText(html, 'html'))

        # Send via SMTP + STARTTLS (port 587) - secure connection, best for cloud hosts
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'], timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
            server.send_message(msg)

        logger.info(f'✅ Email sent to {recipient_email} (STARTTLS port 587) - Subject: {subject}')
        return True
    except smtplib.SMTPAuthenticationError as e:
        error_msg = (
            f"❌ SMTP Authentication FAILED for {EMAIL_CONFIG['sender_email']}. "
            f"Check EMAIL_SENDER and EMAIL_PASSWORD in .env. Error: {e}"
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        logger.error(f'❌ Failed to send email to {recipient_email}: {str(e)}')
        return False


def send_notification_email(
    admin_id: int,
    event_type: str,
    data: Dict,
    recipient_override: Optional[str] = None
) -> bool:
    """
    Send notification email based on event type
    
    Args:
        admin_id: Admin ID for logging
        event_type: Type of event (farmer_pending, product_pending, dispute_open, etc.)
        data: Event data
        recipient_override: Override recipient email
    
    Returns:
        bool: Success/failure
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Get admin email if not overridden
        if not recipient_override:
            cursor.execute('SELECT email FROM admins WHERE admin_id = %s', (admin_id,))
            admin = cursor.fetchone()
            if not admin:
                return False
            recipient_email = admin['email']
        else:
            recipient_email = recipient_override

        # Event-specific email templates
        templates = {
            'farmer_pending': {
                'subject': f"New Farmer Pending Approval - {data.get('farmer_name', 'Unknown')}",
                'body': f"""Dear Admin,

A new farmer has registered and is pending approval:

Name: {data.get('farmer_name')}
Phone: {data.get('phone')}
Location: {data.get('location')}
Land Area: {data.get('land_area')} acres

Action Required: Login to admin panel to review and approve.

Best regards,
Smart Farming Team""",
            },
            'product_pending': {
                'subject': f"Product Pending Review - {data.get('product_name', 'Unknown')}",
                'body': f"""Dear Admin,

A new product has been uploaded and requires review:

Product: {data.get('product_name')}
Farmer: {data.get('farmer_name')}
Category: {data.get('category')}
Price: ₹{data.get('price')}

Action Required: Review and approve/reject in admin panel.

Best regards,
Smart Farming Team""",
            },
            'dispute_open': {
                'subject': f"New Dispute Opened - Order #{data.get('order_id')}",
                'body': f"""Dear Admin,

A new dispute has been filed:

Order ID: {data.get('order_id')}
Buyer: {data.get('buyer_name')}
Farmer: {data.get('farmer_name')}
Type: {data.get('complaint_type')}
Description: {data.get('description')}

Action Required: Investigate and resolve in admin panel.

Best regards,
Smart Farming Team""",
            },
            'refund_pending': {
                'subject': f"Refund Request Pending Approval - ₹{data.get('amount')}",
                'body': f"""Dear Admin,

A refund request requires your approval:

Order ID: {data.get('order_id')}
Buyer: {data.get('buyer_name')}
Amount: ₹{data.get('amount')}
Reason: {data.get('reason')}

Action Required: Approve or reject in admin panel.

Best regards,
Smart Farming Team""",
            },
            'ai_model_accuracy_warning': {
                'subject': 'AI Model Accuracy Warning - Action Required',
                'body': f"""Dear Admin,

AI Model performance warning:

Model Type: {data.get('model_type')}
Current Accuracy: {data.get('accuracy')}%
Threshold: {data.get('threshold')}%

Action Required: Review model performance and retrain if necessary.

Best regards,
Smart Farming Team""",
            },
            'platform_alert': {
                'subject': 'Platform Alert - Immediate Action Required',
                'body': f"""Dear Admin,

System Alert:

Issue: {data.get('issue')}
Severity: {data.get('severity')}
Details: {data.get('details')}

Action Required: Review and take necessary action.

Best regards,
Smart Farming Team""",
            },
        }

        template = templates.get(event_type, {
            'subject': 'Smart Farming Notification',
            'body': f'Notification: {json.dumps(data)}'
        })

        # Send email
        success = send_email(recipient_email, template['subject'], template['body'])

        # Log notification
        if success:
            cursor.execute("""
                INSERT INTO notification_logs (
                    admin_id, event_type, recipient_email, sent_at, status
                ) VALUES (%s, %s, %s, %s, %s)
            """, (admin_id, event_type, recipient_email, datetime.now(), 'sent'))
            db.commit()

        cursor.close()
        db.close()
        return success

    except Exception as e:
        logger.error(f'Error sending notification email: {str(e)}')
        return False


# ==================== WEBHOOK SYSTEM ====================

class WebhookManager:
    """Manages webhook registration, trigger, and retry logic"""

    @staticmethod
    def register_webhook(
        event_type: str,
        webhook_url: str,
        headers: Optional[Dict] = None,
        active: bool = True
    ) -> bool:
        """
        Register webhook endpoint for events
        
        Args:
            event_type: Type of event to subscribe to
            webhook_url: URL to POST events to
            headers: Custom headers to include in webhook calls
            active: Whether webhook is active
        
        Returns:
            bool: Success/failure
        """
        try:
            db = get_db_connection()
            cursor = db.cursor()

            cursor.execute("""
                INSERT INTO webhooks (
                    event_type, webhook_url, custom_headers, active, created_at
                ) VALUES (%s, %s, %s, %s, %s)
            """, (
                event_type,
                webhook_url,
                json.dumps(headers or {}),
                active,
                datetime.now()
            ))

            db.commit()
            cursor.close()
            db.close()
            return True
        except Exception as e:
            logger.error(f'Failed to register webhook: {str(e)}')
            return False

    @staticmethod
    def get_webhooks(event_type: str) -> List[Dict]:
        """
        Get active webhooks for event type
        
        Args:
            event_type: Event type to filter by
        
        Returns:
            List of webhook configurations
        """
        try:
            db = get_db_connection()
            cursor = db.cursor(dictionary=True)

            cursor.execute("""
                SELECT * FROM webhooks
                WHERE event_type = %s AND active = TRUE
            """, (event_type,))

            webhooks = cursor.fetchall()
            cursor.close()
            db.close()
            return webhooks
        except Exception as e:
            logger.error(f'Failed to get webhooks: {str(e)}')
            return []

    @staticmethod
    def trigger_webhooks(event_type: str, data: Dict, retries: int = 3) -> None:
        """
        Trigger all webhooks for event type
        
        Args:
            event_type: Type of event
            data: Event data to send
            retries: Number of retry attempts
        """
        webhooks = WebhookManager.get_webhooks(event_type)

        for webhook in webhooks:
            try:
                # Prepare payload
                payload = {
                    'event': event_type,
                    'timestamp': datetime.now().isoformat(),
                    'data': data,
                }

                # Parse custom headers
                headers = json.loads(webhook['custom_headers'] or '{}')
                headers['Content-Type'] = 'application/json'
                headers['User-Agent'] = 'SmartFarming-Webhook/1.0'

                # Try to deliver webhook with retries
                for attempt in range(retries):
                    try:
                        response = requests.post(
                            webhook['webhook_url'],
                            json=payload,
                            headers=headers,
                            timeout=10
                        )

                        # Log webhook delivery
                        WebhookManager._log_webhook_delivery(
                            webhook['webhook_id'],
                            event_type,
                            response.status_code,
                            'success' if response.status_code < 400 else 'failed'
                        )

                        if response.status_code < 400:
                            break
                    except requests.RequestException as e:
                        if attempt == retries - 1:
                            WebhookManager._log_webhook_delivery(
                                webhook['webhook_id'],
                                event_type,
                                0,
                                'failed',
                                str(e)
                            )
            except Exception as e:
                logger.error(f'Error triggering webhook: {str(e)}')

    @staticmethod
    def _log_webhook_delivery(
        webhook_id: int,
        event_type: str,
        status_code: int,
        status: str,
        error_message: Optional[str] = None
    ) -> None:
        """Log webhook delivery attempt"""
        try:
            db = get_db_connection()
            cursor = db.cursor()

            cursor.execute("""
                INSERT INTO webhook_logs (
                    webhook_id, event_type, status_code, status, error_message, delivered_at
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (webhook_id, event_type, status_code, status, error_message, datetime.now()))

            db.commit()
            cursor.close()
            db.close()
        except Exception as e:
            logger.error(f'Failed to log webhook delivery: {str(e)}')


# ==================== BATCH OPERATIONS ====================

@admin_advanced_features_bp.route('/batch/approve-products', methods=['POST'])
def batch_approve_products():
    """
    Bulk approve multiple products
    
    Request Body:
    {
        "product_ids": [1, 2, 3],
        "notes": "Batch approved"
    }
    """
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        admin_id = verify_token(token)
        if not admin_id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401

        data = request.get_json()
        product_ids = data.get('product_ids', [])
        notes = data.get('notes', '')

        if not product_ids:
            return jsonify({'success': False, 'error': 'No products specified'}), 400

        db = get_db_connection()
        cursor = db.cursor()

        # Approve all products
        for product_id in product_ids:
            cursor.execute("""
                UPDATE products
                SET status = 'approved', approved_by = %s, approved_at = %s
                WHERE product_id = %s AND status = 'pending'
            """, (admin_id, datetime.now(), product_id))

            # Log action
            cursor.execute("""
                INSERT INTO admin_logs (
                    admin_id, action, module, entity_type, entity_id, description, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                admin_id,
                'approve',
                'products',
                'product',
                product_id,
                notes or 'Batch approved',
                datetime.now()
            ))

            # Trigger webhook
            WebhookManager.trigger_webhooks('product_approved', {
                'product_id': product_id,
                'approved_by': admin_id,
                'notes': notes
            })

        db.commit()
        cursor.close()
        db.close()

        return jsonify({
            'success': True,
            'message': f'{len(product_ids)} products approved',
            'count': len(product_ids)
        }), 200

    except Exception as e:
        logger.error(f'Batch approve error: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_advanced_features_bp.route('/batch/block-users', methods=['POST'])
def batch_block_users():
    """
    Bulk block multiple users (farmers/buyers)
    
    Request Body:
    {
        "user_ids": [1, 2, 3],
        "user_type": "farmer",
        "reason": "Policy violation",
        "duration_days": 30
    }
    """
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        admin_id = verify_token(token)
        if not admin_id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401

        data = request.get_json()
        user_ids = data.get('user_ids', [])
        user_type = data.get('user_type', 'farmer')  # farmer or buyer
        reason = data.get('reason', '')
        duration_days = data.get('duration_days', None)

        if not user_ids:
            return jsonify({'success': False, 'error': 'No users specified'}), 400

        db = get_db_connection()
        cursor = db.cursor()

        # Block all users
        for user_id in user_ids:
            expiry_date = None
            if duration_days:
                from datetime import timedelta
                expiry_date = datetime.now() + timedelta(days=duration_days)

            cursor.execute("""
                INSERT INTO user_blocks (
                    user_id, user_type, reason, blocked_by, blocked_at, expiry_date
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, user_type, reason, admin_id, datetime.now(), expiry_date))

            # Log action
            cursor.execute("""
                INSERT INTO admin_logs (
                    admin_id, action, module, entity_type, entity_id, description, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                admin_id,
                'block',
                'users',
                user_type,
                user_id,
                reason,
                datetime.now()
            ))

            # Trigger webhook
            WebhookManager.trigger_webhooks('user_blocked', {
                'user_id': user_id,
                'user_type': user_type,
                'reason': reason,
                'blocked_by': admin_id
            })

        db.commit()
        cursor.close()
        db.close()

        return jsonify({
            'success': True,
            'message': f'{len(user_ids)} users blocked',
            'count': len(user_ids)
        }), 200

    except Exception as e:
        logger.error(f'Batch block error: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_advanced_features_bp.route('/batch/generate-reports', methods=['POST'])
def batch_generate_reports():
    """
    Generate multiple reports in batch
    
    Request Body:
    {
        "report_types": ["sales", "users", "products"],
        "date_from": "2024-01-01",
        "date_to": "2024-01-31"
    }
    """
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        admin_id = verify_token(token)
        if not admin_id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401

        data = request.get_json()
        report_types = data.get('report_types', [])
        date_from = data.get('date_from')
        date_to = data.get('date_to')

        if not report_types:
            return jsonify({'success': False, 'error': 'No report types specified'}), 400

        db = get_db_connection()
        cursor = db.cursor()

        generated_reports = []

        for report_type in report_types:
            try:
                # Generate report based on type
                if report_type == 'sales':
                    cursor.execute("""
                        SELECT COUNT(*) as total_orders, SUM(total_amount) as total_revenue
                        FROM orders
                        WHERE created_at BETWEEN %s AND %s
                    """, (date_from, date_to))
                    report_data = cursor.fetchone()
                
                elif report_type == 'users':
                    cursor.execute("""
                        SELECT COUNT(*) as total_farmers FROM farmers WHERE created_at BETWEEN %s AND %s
                        UNION ALL
                        SELECT COUNT(*) as total_buyers FROM buyers WHERE created_at BETWEEN %s AND %s
                    """, (date_from, date_to, date_from, date_to))
                    report_data = cursor.fetchall()
                
                else:
                    report_data = None

                # Store report
                cursor.execute("""
                    INSERT INTO analytics_reports (
                        report_type, generated_by, report_data, generated_at
                    ) VALUES (%s, %s, %s, %s)
                """, (
                    report_type,
                    admin_id,
                    json.dumps(report_data, default=str),
                    datetime.now()
                ))

                generated_reports.append({
                    'report_type': report_type,
                    'generated_at': datetime.now().isoformat(),
                    'status': 'success'
                })

            except Exception as e:
                logger.error(f'Failed to generate {report_type} report: {str(e)}')
                generated_reports.append({
                    'report_type': report_type,
                    'error': str(e),
                    'status': 'failed'
                })

        db.commit()
        cursor.close()
        db.close()

        return jsonify({
            'success': True,
            'message': f'{len(generated_reports)} reports generated',
            'reports': generated_reports
        }), 200

    except Exception as e:
        logger.error(f'Batch generate reports error: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500


def verify_token(token: str) -> Optional[int]:
    """Verify JWT token and return admin_id (simplified)"""
    try:
        from jwt import decode
        payload = decode(token, os.getenv('SECRET_KEY', 'secret'), algorithms=['HS256'])
        return payload.get('admin_id')
    except:
        return None


# Export
__all__ = ['admin_advanced_features_bp', 'send_notification_email', 'WebhookManager']
