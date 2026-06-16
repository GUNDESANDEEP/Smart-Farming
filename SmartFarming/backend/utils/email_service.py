"""
Email Service - Send Emails for Notifications, OTP, and Password Reset
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

class EmailService:
    """Handle sending emails via SMTP"""
    
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SENDER_EMAIL = os.getenv('SMTP_EMAIL')
    SENDER_PASSWORD = os.getenv('SMTP_PASSWORD')
    
    @staticmethod
    def send_otp_email(recipient_email, otp_code, user_name):
        """Send OTP verification email"""
        try:
            subject = "Smart Farmer Marketplace - Verify Your Email"
            
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #2c5f2d;">Welcome to Smart Farmer Marketplace!</h2>
                        
                        <p>Hi {user_name},</p>
                        
                        <p>To verify your email address and complete your registration, please use the following OTP code:</p>
                        
                        <div style="background-color: #f0f0f0; padding: 20px; text-align: center; margin: 20px 0; border-radius: 5px;">
                            <h1 style="color: #2c5f2d; letter-spacing: 5px; margin: 0;">{otp_code}</h1>
                        </div>
                        
                        <p>This code will expire in 10 minutes.</p>
                        
                        <p>If you didn't request this code, please ignore this email.</p>
                        
                        <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                        
                        <p style="font-size: 12px; color: #666;">
                            Smart Farmer Marketplace<br>
                            {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                        </p>
                    </div>
                </body>
            </html>
            """
            
            return EmailService._send_email(recipient_email, subject, html_body)
        
        except Exception as e:
            print(f"Send OTP email error: {e}")
            return False
    
    @staticmethod
    def send_password_reset_email(recipient_email, reset_token, user_name):
        """Send password reset email"""
        try:
            reset_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={reset_token}"
            
            subject = "Smart Farmer Marketplace - Reset Your Password"
            
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #2c5f2d;">Password Reset Request</h2>
                        
                        <p>Hi {user_name},</p>
                        
                        <p>We received a request to reset your password. Click the link below to create a new password:</p>
                        
                        <p style="text-align: center; margin: 20px 0;">
                            <a href="{reset_url}" style="background-color: #2c5f2d; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                                Reset Password
                            </a>
                        </p>
                        
                        <p>Or copy this link: <a href="{reset_url}">{reset_url}</a></p>
                        
                        <p>This link will expire in 1 hour.</p>
                        
                        <p>If you didn't request this, please ignore this email.</p>
                        
                        <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                        
                        <p style="font-size: 12px; color: #666;">
                            Smart Farmer Marketplace<br>
                            {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                        </p>
                    </div>
                </body>
            </html>
            """
            
            return EmailService._send_email(recipient_email, subject, html_body)
        
        except Exception as e:
            print(f"Send password reset email error: {e}")
            return False
    
    @staticmethod
    def send_welcome_email(recipient_email, user_name, user_role):
        """Send welcome email after registration"""
        try:
            subject = f"Welcome to Smart Farmer Marketplace, {user_name}!"
            
            role_message = "farmer" if user_role == "farmer" else "buyer"
            dashboard_link = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/dashboard"
            
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #2c5f2d;">Welcome, {user_name}!</h2>
                        
                        <p>Thank you for joining Smart Farmer Marketplace as a {role_message}.</p>
                        
                        <p>You're now ready to start using our platform:</p>
                        
                        <ul style="font-size: 16px; line-height: 1.8;">
                            <li>Browse available products</li>
                            <li>Connect with sellers and buyers</li>
                            <li>Make secure transactions</li>
                            <li>Manage your profile and preferences</li>
                        </ul>
                        
                        <p style="text-align: center; margin: 20px 0;">
                            <a href="{dashboard_link}" style="background-color: #2c5f2d; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                                Go to Dashboard
                            </a>
                        </p>
                        
                        <p>If you have any questions, feel free to contact our support team.</p>
                        
                        <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                        
                        <p style="font-size: 12px; color: #666;">
                            Smart Farmer Marketplace<br>
                            {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                        </p>
                    </div>
                </body>
            </html>
            """
            
            return EmailService._send_email(recipient_email, subject, html_body)
        
        except Exception as e:
            print(f"Send welcome email error: {e}")
            return False
    
    @staticmethod
    def send_order_notification_email(recipient_email, user_name, order_number, amount):
        """Send order notification email"""
        try:
            subject = f"Order Confirmation - {order_number}"
            
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #2c5f2d;">Order Confirmation</h2>
                        
                        <p>Hi {user_name},</p>
                        
                        <p>Your order has been successfully placed!</p>
                        
                        <div style="background-color: #f0f0f0; padding: 20px; margin: 20px 0; border-radius: 5px;">
                            <p><strong>Order Number:</strong> {order_number}</p>
                            <p><strong>Amount:</strong> ₹{amount:.2f}</p>
                            <p><strong>Status:</strong> Pending</p>
                        </div>
                        
                        <p>The seller will review your order shortly. You'll receive another email once they accept it.</p>
                        
                        <p>Track your order in your <a href="{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/orders">order history</a>.</p>
                        
                        <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                        
                        <p style="font-size: 12px; color: #666;">
                            Smart Farmer Marketplace<br>
                            {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                        </p>
                    </div>
                </body>
            </html>
            """
            
            return EmailService._send_email(recipient_email, subject, html_body)
        
        except Exception as e:
            print(f"Send order notification email error: {e}")
            return False
    
    @staticmethod
    def send_farmer_verification_email(recipient_email, user_name, status):
        """Send farmer verification notification"""
        try:
            subject = f"Farmer Account {status.title()}"
            
            message = "Your farmer account has been verified! You can now list products and start selling." if status == "verified" else "Your farmer account verification was not approved. Please review and resubmit."
            
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #2c5f2d;">Farmer Account {status.title()}</h2>
                        
                        <p>Hi {user_name},</p>
                        
                        <p>{message}</p>
                        
                        <p>Visit your dashboard to manage your account: <a href="{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/dashboard">Dashboard</a></p>
                        
                        <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                        
                        <p style="font-size: 12px; color: #666;">
                            Smart Farmer Marketplace<br>
                            {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                        </p>
                    </div>
                </body>
            </html>
            """
            
            return EmailService._send_email(recipient_email, subject, html_body)
        
        except Exception as e:
            print(f"Send farmer verification email error: {e}")
            return False
    
    @staticmethod
    def _send_email(recipient_email, subject, html_body):
        """Internal method to send email via SMTP"""
        try:
            # Create email message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = EmailService.SENDER_EMAIL
            message["To"] = recipient_email
            
            # Attach HTML content
            part = MIMEText(html_body, "html")
            message.attach(part)
            
            # Connect to SMTP server and send
            with smtplib.SMTP(EmailService.SMTP_SERVER, EmailService.SMTP_PORT) as server:
                server.starttls()
                server.login(EmailService.SENDER_EMAIL, EmailService.SENDER_PASSWORD)
                server.sendmail(EmailService.SENDER_EMAIL, recipient_email, message.as_string())
            
            print(f"Email sent successfully to {recipient_email}")
            return True
        
        except smtplib.SMTPAuthenticationError:
            print("SMTP Authentication failed. Check your email and password.")
            return False
        
        except smtplib.SMTPException as e:
            print(f"SMTP error: {e}")
            return False
        
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
