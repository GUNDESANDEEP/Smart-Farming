#!/usr/bin/env python3
"""
Direct MySQL Admin Creation Script
Attempts to connect to MySQL and create admin account
"""

import sys
from werkzeug.security import generate_password_hash

# Try different connection methods
def try_mysqldb():
    """Try with MySQLdb"""
    try:
        import MySQLdb
        conn = MySQLdb.connect(
            host='127.0.0.1',  # Try 127.0.0.1 instead of localhost
            user='root',
            passwd='Sandy@7981',
            db='SmartFarmingDB'
        )
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        
        # Check if admins table exists
        cursor.execute("SHOW TABLES LIKE 'admins'")
        if not cursor.fetchone():
            print("⚠️  Table 'admins' does not exist!")
            return None
        
        # Create admin
        email = 'gundesandeep2005@gmail.com'
        password = 'Sandy@7982'
        name = 'Sandeep Gunde'
        role = 'super_admin'
        password_hash = generate_password_hash(password)
        
        cursor.execute(
            """INSERT INTO admins (email, password_hash, first_name, role, created_at)
               VALUES (%s, %s, %s, %s, NOW())""",
            (email, password_hash, name, role)
        )
        conn.commit()
        admin_id = cursor.lastrowid
        cursor.close()
        conn.close()
        
        return admin_id
    except Exception as e:
        print(f"MySQLdb error: {e}")
        return None

def try_mysql_connector():
    """Try with mysql-connector-python"""
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host='127.0.0.1',
            user='root',
            password='Sandy@7981',
            database='SmartFarmingDB'
        )
        cursor = conn.cursor(dictionary=True)
        
        # Check if admins table exists
        cursor.execute("SHOW TABLES LIKE 'admins'")
        if not cursor.fetchone():
            print("⚠️  Table 'admins' does not exist!")
            return None
        
        # Create admin
        email = 'gundesandeep2005@gmail.com'
        password = 'Sandy@7982'
        name = 'Sandeep Gunde'
        role = 'super_admin'
        password_hash = generate_password_hash(password)
        
        cursor.execute(
            """INSERT INTO admins (email, password_hash, first_name, role, created_at)
               VALUES (%s, %s, %s, %s, NOW())""",
            (email, password_hash, name, role)
        )
        conn.commit()
        admin_id = cursor.lastrowid
        cursor.close()
        conn.close()
        
        return admin_id
    except Exception as e:
        print(f"mysql-connector error: {e}")
        return None

if __name__ == '__main__':
    print("=" * 70)
    print("ADMIN ACCOUNT CREATION - DIRECT DATABASE")
    print("=" * 70)
    print()
    
    print("Attempting connection with MySQLdb...")
    admin_id = try_mysqldb()
    if admin_id:
        print("✅ Success with MySQLdb!")
        print(f"   Admin ID: {admin_id}")
        sys.exit(0)
    
    print()
    print("Attempting connection with mysql-connector-python...")
    admin_id = try_mysql_connector()
    if admin_id:
        print("✅ Success with mysql-connector-python!")
        print(f"   Admin ID: {admin_id}")
        sys.exit(0)
    
    print()
    print("❌ All connection methods failed!")
    print()
    print("Please verify:")
    print("  1. MySQL service is running")
    print("  2. Database 'SmartFarmingDB' exists")
    print("  3. Credentials are correct: root / Sandy@7981")
    print("  4. Admin table exists in the database")
    sys.exit(1)
