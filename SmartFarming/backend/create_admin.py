"""
Script to create admin user using Flask app context
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import app, mysql
from werkzeug.security import generate_password_hash

with app.app_context():
    try:
        # Admin credentials
        email = 'gundesandeep2005@gmail.com'
        password = 'Sandy@7982'
        name = 'Sandeep Gunde'
        
        # Hash the password
        password_hash = generate_password_hash(password)
        
        cursor = mysql.connection.cursor()
        
        # Check if admin already exists
        check_query = "SELECT * FROM admins WHERE email = %s"
        cursor.execute(check_query, (email,))
        existing_admin = cursor.fetchone()
        
        if existing_admin:
            print(f"✅ Admin already exists with email: {email}")
            if existing_admin:
                print(f"   Record: {existing_admin}")
        else:
            # Create new admin
            insert_query = """
                INSERT INTO admins (email, password_hash, name, role, created_at)
                VALUES (%s, %s, %s, %s, NOW())
            """
            cursor.execute(insert_query, (email, password_hash, name, 'super_admin'))
            mysql.connection.commit()
            
            print(f"✅ Admin created successfully!")
            print(f"   Email: {email}")
            print(f"   Password: {password}")
            print(f"   Name: {name}")
            print(f"   Role: super_admin")
            print(f"   Admin ID: {cursor.lastrowid}")
        
        cursor.close()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
