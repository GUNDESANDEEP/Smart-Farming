#!/usr/bin/env python3
"""
Flask Shell Commands for Admin Setup
Run with: flask shell
Then execute the create_admin function
"""

import sys
sys.path.insert(0, '.')

from app import app, mysql
from werkzeug.security import generate_password_hash

@app.shell_context_processor
def make_shell_context():
    def create_admin_account():
        """Create admin account"""
        email = 'gundesandeep2005@gmail.com'
        password = 'Sandy@7982'
        name = 'Sandeep Gunde'
        role = 'super_admin'
        
        try:
            password_hash = generate_password_hash(password)
            
            cursor = mysql.connection.cursor()
            cursor.execute(
                """INSERT INTO admins (email, password_hash, first_name, role, created_at)
                   VALUES (%s, %s, %s, %s, NOW())""",
                (email, password_hash, name, role)
            )
            mysql.connection.commit()
            admin_id = cursor.lastrowid
            cursor.close()
            
            print(f"✅ Admin created successfully!")
            print(f"   ID: {admin_id}")
            print(f"   Email: {email}")
            print(f"   Role: {role}")
            return True
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False
    
    return {'create_admin_account': create_admin_account}

if __name__ == '__main__':
    with app.app_context():
        print("Flask Shell Context Created")
        print("Run: python -c \"from flask import Flask; app = Flask(__name__); import create_admin\"")
        print("Or: flask shell")
        print("Then in shell: create_admin_account()")
