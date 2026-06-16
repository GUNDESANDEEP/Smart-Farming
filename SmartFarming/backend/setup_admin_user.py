#!/usr/bin/env python3
"""
Simple admin setup script
Creates admin user directly without Flask app initialization
"""
import mysql.connector
from werkzeug.security import generate_password_hash
import sys

# Database credentials from .env
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'Sandy@7981'
DB_NAME = 'SmartFarmingDB'

# Admin credentials
ADMIN_EMAIL = 'admin@smartfarming.com'
ADMIN_PASSWORD = 'admin123'
ADMIN_NAME = 'Admin User'

try:
    print("Connecting to database...")
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    
    cursor = conn.cursor()
    
    # Check if admin already exists
    cursor.execute("SELECT COUNT(*) FROM admins WHERE email = %s", (ADMIN_EMAIL,))
    result = cursor.fetchone()
    
    if result[0] > 0:
        print(f"✓ Admin user already exists: {ADMIN_EMAIL}")
        cursor.close()
        conn.close()
        sys.exit(0)
    
    # Create password hash
    password_hash = generate_password_hash(ADMIN_PASSWORD)
    
    # Insert admin
    print(f"Creating admin user: {ADMIN_EMAIL}")
    cursor.execute(
        """INSERT INTO admins (email, password_hash, first_name, role, is_active, created_at)
           VALUES (%s, %s, %s, %s, %s, NOW())""",
        (ADMIN_EMAIL, password_hash, ADMIN_NAME, 'super_admin', 1)
    )
    conn.commit()
    
    admin_id = cursor.lastrowid
    print(f"✓ Admin created successfully!")
    print(f"  - Admin ID: {admin_id}")
    print(f"  - Email: {ADMIN_EMAIL}")
    print(f"  - Password: {ADMIN_PASSWORD}")
    print(f"  - Role: super_admin")
    
    cursor.close()
    conn.close()
    
except mysql.connector.Error as e:
    print(f"✗ Database error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)
