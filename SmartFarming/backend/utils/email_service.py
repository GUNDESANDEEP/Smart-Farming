"""
Email Service - Send Emails for Notifications, OTP, and Password Reset
Uses Gmail SMTP for reliable email delivery.

Anti-Spam Best Practices Applied:
- Proper sender display name
- Both text/plain and text/html MIME parts
- Proper DOCTYPE and HTML structure
- Consistent From name
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os
import sys
import re
from datetime import datetime

load_dotenv()


# ============================================================================
# SMTP CONFIGURATION
# ============================================================================

SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
EMAIL_SENDER = os.getenv('EMAIL_SENDER', '')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
EMAIL_FROM_NAME = os.getenv('EMAIL_FROM_NAME', 'SmartFarming')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', '')
FLASK_ENV = os.getenv('FLASK_ENV', 'development')


def is_dev_mode():
    """Check if running in development mode."""
    return FLASK_ENV in ('development', 'dev', 'local')


# ============================================================================
# BRANDED EMAIL TEMPLATE (matches the "good" email with leaf icon)
# ============================================================================

def _build_email_html(title, body_content, footer_text=""):
    """Build a branded HTML email that won't go to spam.
    Matches the 'good' email format with leaf icon and proper structure."""
    year = datetime.now().year
    return f"""<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
</head>
<body style="margin:0; padding:0; background-color:#f4f4f4; font-family: 'Segoe UI', Arial, sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f4; padding:30px 0;">
    <tr>
      <td align="center">
        <table role="presentation" width="460" cellpadding="0" cellspacing="0" style="background:#ffffff; border-radius:16px; overflow:hidden; box-shadow:0 2px 12px rgba(0,0,0,0.08);">
          <!-- Header with leaf icon -->
          <tr>
            <td style="background: linear-gradient(135deg, #f0fdf4, #dcfce7); padding:28px 30px 18px; text-align:center;">
              <div style="font-size:28px; margin-bottom:6px;">&#127807;</div>
              <h1 style="margin:0; font-size:22px; font-weight:700; color:#166534; letter-spacing:0.5px;">SmartFarm</h1>
            </td>
          </tr>
          <!-- Body -->
          <tr>
            <td style="padding:24px 30px 28px;">
              {body_content}
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="background:#f9fafb; padding:16px 30px; border-top:1px solid #e5e7eb; text-align:center;">
              <p style="margin:0; font-size:12px; color:#9ca3af;">
                {footer_text if footer_text else f'&copy; {year} SmartFarm Marketplace. All rights reserved.'}
              </p>
              <p style="margin:4px 0 0; font-size:11px; color:#d1d5db;">
                This is an automated message. Please do not reply directly.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _build_otp_html(purpose_text, otp_code, expiry_text="Valid for 10 minutes"):
    """Build branded OTP email body content."""
    body = f"""
    <h2 style="margin:0 0 8px; font-size:17px; font-weight:600; color:#1f2937; text-align:center;">{purpose_text}</h2>
    <div style="text-align:center; margin:22px 0;">
      <span style="display:inline-block; font-size:32px; font-weight:800; letter-spacing:10px; color:#15803d; background:#f0fdf4; padding:14px 28px; border-radius:12px; border:2px dashed #86efac;">{otp_code}</span>
    </div>
    <p style="text-align:center; margin:0; font-size:13px; color:#6b7280;">{expiry_text}</p>
    <p style="text-align:center; margin:8px 0 0; font-size:12px; color:#9ca3af;">If you didn't request this, please ignore this email.</p>
    """
    return _build_email_html(purpose_text, body)


def _build_plaintext_otp(purpose_text, otp_code, expiry_text="Valid for 10 minutes"):
    """Build plain text fallback for OTP emails."""
    return f"""SmartFarm - {purpose_text}

Your OTP code is: {otp_code}

{expiry_text}

If you didn't request this, please ignore this email.

- SmartFarm Marketplace Team
"""


def _html_to_plaintext(html_body):
    """Strip HTML tags to create a plain text fallback."""
    plain = re.sub(r'<[^>]+>', '', html_body).strip()
    plain = re.sub(r'\s+', ' ', plain)
    return plain


class EmailService:
    """Handle sending emails via SMTP (Gmail)"""
    
    SENDER_NAME = 'SmartFarm'
    
    @classmethod
    def validate_config(cls):
        """
        Validate that SMTP credentials are configured.
        Raises RuntimeError if missing - SMTP config is mandatory.
        """
        if not EMAIL_SENDER or not EMAIL_PASSWORD:
            env = os.getenv('ENVIRONMENT', os.getenv('FLASK_ENV', 'development')).lower()
            error_msg = (
                f"\n{'='*60}\n"
                f"  SMTP EMAIL CONFIG NOT SET\n"
                f"{'='*60}\n"
                f"  EMAIL_SENDER or EMAIL_PASSWORD is not configured in .env\n\n"
                f"  Required .env variables:\n"
                f"    SMTP_HOST=smtp.gmail.com\n"
                f"    SMTP_PORT=587\n"
                f"    EMAIL_SENDER=your_email@gmail.com\n"
                f"    EMAIL_PASSWORD=your_app_password\n"
                f"    EMAIL_FROM_NAME=SmartFarming\n"
                f"{'='*60}\n"
            )
            print(error_msg, file=sys.stderr)
            if env == 'production':
                raise RuntimeError("SMTP configuration incomplete: missing EMAIL_SENDER or EMAIL_PASSWORD")
            print("[WARN] SMTP not configured — email features disabled in development")
            return False
        
        print(f"[OK] SMTP email configured - Host: {SMTP_HOST}:{SMTP_PORT}, From: {EMAIL_FROM_NAME} <{EMAIL_SENDER}>")
        return True
    
    # Keep backward-compatible alias
    @classmethod
    def validate_smtp_config(cls):
        """Backward-compatible alias for validate_config."""
        return cls.validate_config()
    
    @staticmethod
    def send_otp_email(recipient_email, otp_code, user_name):
        """Send OTP verification email"""
        try:
            subject = "SmartFarm - Verify Your Email"
            
            body_content = f"""
            <p style="margin:0 0 12px; font-size:15px; color:#374151;">Hi <strong>{user_name}</strong>,</p>
            <p style="margin:0 0 4px; font-size:14px; color:#4b5563;">To verify your email and complete registration, use this OTP:</p>
            """
            body_content += f"""
            <div style="text-align:center; margin:22px 0;">
              <span style="display:inline-block; font-size:32px; font-weight:800; letter-spacing:10px; color:#15803d; background:#f0fdf4; padding:14px 28px; border-radius:12px; border:2px dashed #86efac;">{otp_code}</span>
            </div>
            <p style="text-align:center; margin:0; font-size:13px; color:#6b7280;">Valid for 10 minutes</p>
            <p style="text-align:center; margin:8px 0 0; font-size:12px; color:#9ca3af;">If you didn't request this code, please ignore this email.</p>
            """
            
            html_body = _build_email_html(subject, body_content)
            
            return EmailService._send_email(recipient_email, subject, html_body)
        
        except Exception as e:
            print(f"Send OTP email error: {e}")
            return False
    
    @staticmethod
    def send_otp_email_safe(recipient_email, otp_code, purpose='login', user_name='User'):
        """
        Send OTP email via SMTP.
        
        Returns a dict:
          - {"sent": True}  — email was sent successfully
          - {"sent": False, "reason": "send_failed"} — email failed,
            caller should handle gracefully
          - {"sent": False, "error": "..."} — actual error
        """
        # Determine subject and body based on purpose
        subject_map = {
            'login': 'SmartFarm - Login OTP',
            'verification': 'SmartFarm - Verify Your Email',
            'email_verification': 'SmartFarm - Verify Your Email',
            'password_reset': 'SmartFarm - Password Reset OTP',
            'forgot_password': 'SmartFarm - Password Reset OTP',
        }
        purpose_text_map = {
            'login': 'Your login verification OTP is:',
            'verification': 'Your email verification OTP is:',
            'email_verification': 'Your email verification OTP is:',
            'password_reset': 'Your password reset OTP is:',
            'forgot_password': 'Your password reset OTP is:',
        }
        expiry_map = {
            'login': 'Valid for 5 minutes',
            'verification': 'Valid for 10 minutes',
            'email_verification': 'Valid for 10 minutes',
            'password_reset': 'Valid for 10 minutes',
            'forgot_password': 'Valid for 10 minutes',
        }
        
        subject = subject_map.get(purpose, 'SmartFarm - OTP Verification')
        purpose_text = purpose_text_map.get(purpose, 'Your OTP is:')
        expiry_text = expiry_map.get(purpose, 'Valid for 10 minutes')
        
        html_body = _build_otp_html(purpose_text, otp_code, expiry_text)
        
        try:
            email_sent = EmailService._send_email(recipient_email, subject, html_body)
            if email_sent:
                return {"sent": True}
            else:
                print(f"[OTP] Email send returned False for {recipient_email}")
                return {"sent": False, "reason": "send_failed"}
        except Exception as e:
            print(f"[OTP] Email send exception for {recipient_email}: {e}")
            return {"sent": False, "error": "Failed to send OTP email"}
    
    @staticmethod
    def send_password_reset_email(recipient_email, reset_token, user_name):
        """Send password reset email"""
        try:
            subject = "SmartFarm - Password Reset OTP"
            
            html_body = _build_otp_html("Your password reset OTP is:", reset_token)
            
            return EmailService._send_email(recipient_email, subject, html_body)
        
        except Exception as e:
            print(f"Send password reset email error: {e}")
            return False
    
    @staticmethod
    def send_welcome_email(recipient_email, user_name, user_role):
        """Send welcome email after registration"""
        try:
            subject = f"Welcome to SmartFarm, {user_name}!"
            
            role_message = "farmer" if user_role == "farmer" else "buyer"
            dashboard_link = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/dashboard"
            
            body_content = f"""
            <h2 style="margin:0 0 12px; font-size:18px; color:#166534;">Welcome, {user_name}! 🎉</h2>
            <p style="font-size:14px; color:#374151; line-height:1.6;">Thank you for joining SmartFarm as a <strong>{role_message}</strong>. You're now ready to start using our platform:</p>
            <ul style="font-size:14px; color:#374151; line-height:2; padding-left:20px;">
              <li>Browse available products</li>
              <li>Connect with sellers and buyers</li>
              <li>Make secure transactions</li>
              <li>Manage your profile and preferences</li>
            </ul>
            <div style="text-align:center; margin:20px 0;">
              <a href="{dashboard_link}" style="display:inline-block; background:linear-gradient(135deg, #166534, #22c55e); color:#fff; padding:12px 28px; border-radius:10px; text-decoration:none; font-weight:700; font-size:14px;">Go to Dashboard →</a>
            </div>
            <p style="font-size:13px; color:#6b7280;">If you have any questions, feel free to contact our support team.</p>
            """
            
            html_body = _build_email_html(subject, body_content)
            
            return EmailService._send_email(recipient_email, subject, html_body)
        
        except Exception as e:
            print(f"Send welcome email error: {e}")
            return False
    
    @staticmethod
    def send_order_notification_email(recipient_email, user_name, order_number, amount):
        """Send order notification email"""
        try:
            subject = f"SmartFarm - Order Confirmation #{order_number}"
            
            body_content = f"""
            <p style="font-size:14px; color:#374151;">Hi <strong>{user_name}</strong>,</p>
            <p style="font-size:14px; color:#374151;">Your order has been successfully placed!</p>
            <div style="background:#f0fdf4; padding:16px 20px; border-radius:12px; margin:16px 0; border:1px solid #dcfce7;">
              <p style="margin:4px 0; font-size:14px; color:#374151;"><strong>Order:</strong> #{order_number}</p>
              <p style="margin:4px 0; font-size:14px; color:#374151;"><strong>Amount:</strong> ₹{amount:.2f}</p>
              <p style="margin:4px 0; font-size:14px; color:#374151;"><strong>Status:</strong> Pending</p>
            </div>
            <p style="font-size:13px; color:#6b7280;">The seller will review your order shortly. You'll receive another email once they accept it.</p>
            """
            
            html_body = _build_email_html(subject, body_content)
            
            return EmailService._send_email(recipient_email, subject, html_body)
        
        except Exception as e:
            print(f"Send order notification email error: {e}")
            return False
    
    @staticmethod
    def send_farmer_verification_email(recipient_email, user_name, status):
        """Send farmer verification notification"""
        try:
            subject = f"SmartFarm - Farmer Account {status.title()}"
            
            if status == "verified":
                message = "Your farmer account has been verified! You can now list products and start selling."
                icon = "✅"
            else:
                message = "Your farmer account verification was not approved. Please review and resubmit."
                icon = "⚠️"
            
            dashboard_link = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/dashboard"
            
            body_content = f"""
            <p style="font-size:14px; color:#374151;">Hi <strong>{user_name}</strong>,</p>
            <div style="text-align:center; margin:16px 0; font-size:36px;">{icon}</div>
            <p style="text-align:center; font-size:15px; color:#374151; font-weight:600;">{message}</p>
            <div style="text-align:center; margin:20px 0;">
              <a href="{dashboard_link}" style="display:inline-block; background:linear-gradient(135deg, #166534, #22c55e); color:#fff; padding:12px 28px; border-radius:10px; text-decoration:none; font-weight:700; font-size:14px;">Go to Dashboard</a>
            </div>
            """
            
            html_body = _build_email_html(subject, body_content)
            
            return EmailService._send_email(recipient_email, subject, html_body)
        
        except Exception as e:
            print(f"Send farmer verification email error: {e}")
            return False
    
    @staticmethod
    def _send_email(recipient_email, subject, html_body, plain_body=None):
        """Internal method to send email via SMTP (Gmail).
        
        Uses smtplib with STARTTLS for secure email delivery.
        """
        if not plain_body:
            plain_body = _html_to_plaintext(html_body)
        
        if not EMAIL_SENDER or not EMAIL_PASSWORD:
            print(f"[ERROR] SMTP not configured. Set EMAIL_SENDER + EMAIL_PASSWORD in .env")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{EMAIL_FROM_NAME} <{EMAIL_SENDER}>"
            msg['To'] = recipient_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(plain_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))
            
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.send_message(msg)
            
            print(f"[OK] Email sent via SMTP to {recipient_email}")
            return True
        except Exception as e:
            print(f"[ERROR] SMTP email failed for {recipient_email}: {e}")
            return False


# Validate SMTP at module load time - app will fail to start without valid config
EmailService.validate_config()
