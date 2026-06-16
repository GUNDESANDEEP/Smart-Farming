#!/usr/bin/env python3
"""
Admin Setup Script using Flask App Context
This runs within the Flask app context to use the existing database connection
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from app import app, mysql
from models.models import Admin
from werkzeug.security import generate_password_hash

def create_admin_account():
    """Create admin account using Flask app context"""
    
    with app.app_context():
        try:
            # Admin credentials
            email = 'gundesandeep2005@gmail.com'
            password = 'Sandy@7982'
            first_name = 'Sandeep Gunde'
            role = 'super_admin'
            
            print("=" * 70)
            print("CREATING ADMIN ACCOUNT")
            print("=" * 70)
            print(f"Email: {email}")
            print(f"Name: {first_name}")
            print(f"Role: {role}")
            print()
            
            # Check if admin already exists
            admin = Admin()
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM admins")
            result = cursor.fetchone()
            admin_count = result['count'] if result else 0
            cursor.close()
            
            if admin_count > 0:
                print("⚠️  Admin account already exists!")
                cursor = mysql.connection.cursor()
                cursor.execute("SELECT email, role FROM admins LIMIT 1")
                existing = cursor.fetchone()
                cursor.close()
                if existing:
                    print(f"   Existing admin: {existing['email']} ({existing['role']})")
                print()
                return False
            
            # Check if this email exists
            existing_admin = admin.get_admin_by_email(email)
            if existing_admin:
                print(f"❌ Admin with email {email} already exists!")
                print()
                return False
            
            # Generate password hash
            password_hash = generate_password_hash(password)
            print(f"✓ Password hash generated")
            print()
            
            # Create admin
            admin_id = admin.create_admin(
                email=email,
                password_hash=password_hash,
                first_name=first_name,
                role=role
            )
            
            if admin_id:
                print("=" * 70)
                print("✅ ADMIN ACCOUNT CREATED SUCCESSFULLY!")
                print("=" * 70)
                print()
                print(f"Admin ID: {admin_id}")
                print(f"Email: {email}")
                print(f"Name: {first_name}")
                print(f"Role: {role}")
                print()
                print("You can now login with:")
                print(f"  Email: {email}")
                print(f"  Password: {password}")
                print()
                print("=" * 70)
                return True
            else:
                print("❌ Failed to create admin account!")
                print()
                return False
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = create_admin_account()
    sys.exit(0 if success else 1)
