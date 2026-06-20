from flask import Blueprint, request, jsonify
from functools import wraps
from datetime import datetime
from models.models import BaseModel
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
        from email.utils import formataddr
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = formataddr(('SmartFarm', EMAIL_CONFIG['sender_email']))
        msg['To'] = recipient_email
        msg['Reply-To'] = EMAIL_CONFIG['sender_email']

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
        # Get admin email if not overridden
        if not recipient_override:
            admin = BaseModel.execute_query(
                'SELECT email FROM admins WHERE admin_id = %s', (admin_id,), fetch_one=True
            )
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

        # Log notification (graceful - tables may not exist yet)
        if success:
            try:
                BaseModel.execute_query("""
                    INSERT INTO admin_activity_log (admin_id, action, module, created_at)
                    VALUES (%s, %s, %s, NOW())
                """, (admin_id, f'email_notification:{event_type}', 'notifications'))
            except Exception:
                pass  # Table may not exist

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
        """Register webhook endpoint for events"""
        try:
            BaseModel.execute_insert("""
                INSERT INTO admin_activity_log (admin_id, action, module, created_at)
                VALUES (0, %s, 'webhooks', NOW())
            """, (f'register_webhook:{event_type}:{webhook_url}',))
            return True
        except Exception as e:
            logger.error(f'Failed to register webhook: {str(e)}')
            return False

    @staticmethod
    def get_webhooks(event_type: str) -> List[Dict]:
        """Get active webhooks for event type — simplified without dedicated webhook table"""
        return []

    @staticmethod
    def trigger_webhooks(event_type: str, data: Dict, retries: int = 3) -> None:
        """Trigger all webhooks for event type"""
        webhooks = WebhookManager.get_webhooks(event_type)
        for webhook in webhooks:
            try:
                payload = {
                    'event': event_type,
                    'timestamp': datetime.now().isoformat(),
                    'data': data,
                }
                headers = json.loads(webhook.get('custom_headers', '{}'))
                headers['Content-Type'] = 'application/json'
                headers['User-Agent'] = 'SmartFarming-Webhook/1.0'

                for attempt in range(retries):
                    try:
                        response = requests.post(
                            webhook['webhook_url'],
                            json=payload,
                            headers=headers,
                            timeout=10
                        )
                        if response.status_code < 400:
                            break
                    except requests.RequestException as e:
                        if attempt == retries - 1:
                            logger.error(f'Webhook delivery failed: {e}')
            except Exception as e:
                logger.error(f'Error triggering webhook: {str(e)}')


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

        approved = 0
        for product_id in product_ids:
            result = BaseModel.execute_query("""
                UPDATE products
                SET status = 'approved', updated_at = NOW()
                WHERE id = %s AND status = 'pending'
            """, (product_id,))
            if result:
                approved += 1

            # Log action
            try:
                BaseModel.execute_insert("""
                    INSERT INTO admin_activity_log (admin_id, action, module, target_id, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                """, (admin_id, 'approve_product', 'products', product_id))
            except Exception:
                pass

            # Trigger webhook
            WebhookManager.trigger_webhooks('product_approved', {
                'product_id': product_id,
                'approved_by': admin_id,
                'notes': notes
            })

        return jsonify({
            'success': True,
            'message': f'{approved} products approved',
            'count': approved
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
        user_type = data.get('user_type', 'farmer')
        reason = data.get('reason', '')

        if not user_ids:
            return jsonify({'success': False, 'error': 'No users specified'}), 400

        blocked = 0
        table = 'farmers' if user_type == 'farmer' else 'buyers'
        for user_id in user_ids:
            result = BaseModel.execute_query(f"""
                UPDATE {table} SET is_verified = FALSE WHERE id = %s
            """, (user_id,))
            if result:
                blocked += 1

            # Log action
            try:
                BaseModel.execute_insert("""
                    INSERT INTO admin_activity_log (admin_id, action, module, target_id, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                """, (admin_id, f'block_{user_type}', 'users', user_id))
            except Exception:
                pass

            # Trigger webhook
            WebhookManager.trigger_webhooks('user_blocked', {
                'user_id': user_id,
                'user_type': user_type,
                'reason': reason,
                'blocked_by': admin_id
            })

        return jsonify({
            'success': True,
            'message': f'{blocked} users blocked',
            'count': blocked
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

        generated_reports = []

        for report_type in report_types:
            try:
                if report_type == 'sales':
                    report_data = BaseModel.execute_query("""
                        SELECT COUNT(*) as total_orders, COALESCE(SUM(total_amount), 0) as total_revenue
                        FROM orders
                        WHERE created_at BETWEEN %s AND %s
                    """, (date_from, date_to), fetch_one=True)
                
                elif report_type == 'users':
                    farmers = BaseModel.execute_query("""
                        SELECT COUNT(*) as count FROM farmers WHERE created_at BETWEEN %s AND %s
                    """, (date_from, date_to), fetch_one=True)
                    buyers = BaseModel.execute_query("""
                        SELECT COUNT(*) as count FROM buyers WHERE created_at BETWEEN %s AND %s
                    """, (date_from, date_to), fetch_one=True)
                    report_data = {
                        'total_farmers': farmers['count'] if farmers else 0,
                        'total_buyers': buyers['count'] if buyers else 0
                    }
                
                else:
                    report_data = None

                generated_reports.append({
                    'report_type': report_type,
                    'data': report_data,
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
