"""
Test SMTP Authentication
Verify that your email credentials are correct and SMTP connection works
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os
import sys

# Load environment variables
load_dotenv()

def test_smtp_connection():
    """Test SMTP connection and authentication"""
    
    SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    EMAIL_SENDER = os.getenv('EMAIL_SENDER')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    
    print("=" * 70)
    print("SMTP AUTHENTICATION TEST")
    print("=" * 70)
    print(f"\nSMTP Server: {SMTP_HOST}")
    print(f"SMTP Port: {SMTP_PORT}")
    print(f"Email Sender: {EMAIL_SENDER}")
    print(f"Password length: {len(EMAIL_PASSWORD) if EMAIL_PASSWORD else 0} chars")
    
    # Validate credentials
    if not EMAIL_SENDER:
        print("\n❌ ERROR: EMAIL_SENDER not set in .env")
        return False
    
    if not EMAIL_PASSWORD:
        print("\n❌ ERROR: EMAIL_PASSWORD not set in .env")
        return False
    
    print("\n" + "-" * 70)
    print("Testing SMTP connection...")
    print("-" * 70)
    
    try:
        # Connect to SMTP server
        print(f"[1/4] Connecting to {SMTP_HOST}:{SMTP_PORT}...")
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15)
        print("✅ Connected!")
        
        # Send EHLO
        print("[2/4] Sending EHLO command...")
        server.ehlo()
        print("✅ EHLO sent!")
        
        # Start TLS
        print("[3/4] Starting TLS...")
        server.starttls()
        server.ehlo()
        print("✅ TLS started!")
        
        # Login
        print(f"[4/4] Logging in with {EMAIL_SENDER}...")
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        print("✅ Login successful!")
        
        # Try sending a test email
        print("\n" + "-" * 70)
        print("Sending test email...")
        print("-" * 70)
        
        message = MIMEMultipart("alternative")
        message["Subject"] = "SMTP Test - SmartFarming"
        message["From"] = EMAIL_SENDER
        message["To"] = EMAIL_SENDER
        
        html_body = """
        <html>
            <body style="font-family: Arial, sans-serif;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c5f2d;">✅ SMTP Authentication Successful!</h2>
                    <p>This is a test email to verify your SMTP configuration is working correctly.</p>
                    <p>If you received this email, your email service is configured properly.</p>
                </div>
            </body>
        </html>
        """
        
        part = MIMEText(html_body, "html")
        message.attach(part)
        
        server.sendmail(EMAIL_SENDER, EMAIL_SENDER, message.as_string())
        print(f"✅ Test email sent to {EMAIL_SENDER}!")
        
        server.quit()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED - SMTP IS CONFIGURED CORRECTLY!")
        print("=" * 70)
        return True
    
    except smtplib.SMTPAuthenticationError as e:
        print(f"\n❌ AUTHENTICATION ERROR: {e}")
        print("\nCommon causes:")
        print("  1. Incorrect email or password")
        print("  2. For Gmail, you need to use an 'App Password' (not your Gmail password)")
        print("  3. Less secure app access is disabled")
        print("\nFix for Gmail:")
        print("  - Enable 2-Step Verification: https://myaccount.google.com/security")
        print("  - Create App Password: https://myaccount.google.com/apppasswords")
        print("  - Use the 16-character password in EMAIL_PASSWORD")
        return False
    
    except smtplib.SMTPException as e:
        print(f"\n❌ SMTP ERROR: {e}")
        print("\nCommon causes:")
        print("  1. SMTP host/port is incorrect")
        print("  2. Network connectivity issue")
        print("  3. Firewall blocking port 587")
        return False
    
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_smtp_connection()
    sys.exit(0 if success else 1)
