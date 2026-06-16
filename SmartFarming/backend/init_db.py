"""
Database Initialization Script - Complete setup for Smart Farmer Marketplace
Creates database, tables, and default users
"""

import os
import sys
import MySQLdb
from dotenv import load_dotenv
from datetime import datetime
from werkzeug.security import generate_password_hash
import uuid

load_dotenv()

def get_db_connection():
    """Get MySQL connection (without database)"""
    try:
        conn = MySQLdb.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            user=os.getenv('MYSQL_USER', 'root'),
            passwd=os.getenv('MYSQL_PASSWORD', ''),
            charset='utf8mb4'
        )
        return conn
    except MySQLdb.Error as e:
        print(f"✗ Database connection failed: {e}")
        return None

def create_database():
    """Create database if it doesn't exist"""
    print("\n" + "="*60)
    print("CREATING DATABASE")
    print("="*60)
    
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    db_name = os.getenv('MYSQL_DB', 'smart_farming')
    
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"✓ Database '{db_name}' created successfully")
        conn.commit()
        return True
    
    except MySQLdb.Error as e:
        print(f"✗ Error creating database: {e}")
        return False
    
    finally:
        cursor.close()
        conn.close()

def import_schema():
    """Import database schema"""
    print("\n" + "="*60)
    print("IMPORTING DATABASE SCHEMA")
    print("="*60)
    
    schema_file = 'database/complete_schema.sql'
    
    if not os.path.exists(schema_file):
        print(f"✗ Schema file not found: {schema_file}")
        return False
    
    try:
        db_name = os.getenv('MYSQL_DB', 'smart_farming')
        
        # Read schema file
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_content = f.read()
        
        # Connect to database
        conn = MySQLdb.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            user=os.getenv('MYSQL_USER', 'root'),
            passwd=os.getenv('MYSQL_PASSWORD', ''),
            db=db_name,
            charset='utf8mb4'
        )
        
        cursor = conn.cursor()
        
        # Split schema into statements and execute
        statements = schema_content.split(';')
        for statement in statements:
            statement = statement.strip()
            if statement:
                cursor.execute(statement)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✓ Schema imported successfully")
        return True
    
    except Exception as e:
        print(f"✗ Error importing schema: {e}")
        return False

def create_admin_user():
    """Create default admin user"""
    print("\n" + "="*60)
    print("CREATE ADMIN USER")
    print("="*60)
    
    # Get admin credentials
    print("\nEnter admin user details:")
    email = input("Email (default: admin@smartfarmer.com): ").strip() or "admin@smartfarmer.com"
    password = input("Password: ").strip()
    
    if not password:
        print("✗ Password cannot be empty")
        return False
    
    if len(password) < 8:
        print("✗ Password must be at least 8 characters")
        return False
    
    try:
        db_name = os.getenv('MYSQL_DB', 'smart_farming')
        
        conn = MySQLdb.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            user=os.getenv('MYSQL_USER', 'root'),
            passwd=os.getenv('MYSQL_PASSWORD', ''),
            db=db_name,
            charset='utf8mb4',
            cursorclass=MySQLdb.cursors.DictCursor
        )
        
        cursor = conn.cursor()
        
        # Check if admin already exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            print(f"✗ Admin with email '{email}' already exists")
            cursor.close()
            conn.close()
            return False
        
        # Create user
        hashed_password = generate_password_hash(password)
        user_id = uuid.uuid4().hex[:16]
        
        cursor.execute("""
            INSERT INTO users (id, email, phone, password_hash, first_name, last_name, 
                             role_name, is_verified, is_email_verified, is_active, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id, email, '', hashed_password, 'Admin', 'User', 'admin',
            True, True, True, datetime.now()
        ))
        
        # Create admin profile
        admin_id = uuid.uuid4().hex[:16]
        cursor.execute("""
            INSERT INTO admins (id, user_id, created_at)
            VALUES (%s, %s, %s)
        """, (admin_id, user_id, datetime.now()))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✓ Admin user created successfully")
        print(f"  Email: {email}")
        print(f"  Role: Admin")
        
        return True
    
    except MySQLdb.Error as e:
        print(f"✗ Error creating admin user: {e}")
        return False

def verify_tables():
    """Verify all tables were created"""
    print("\n" + "="*60)
    print("VERIFYING TABLES")
    print("="*60)
    
    required_tables = [
        'users', 'roles', 'farmers', 'buyers', 'admins',
        'products', 'categories', 'orders', 'order_items',
        'payments', 'carts', 'cart_items', 'reviews',
        'messages', 'conversations', 'notifications',
        'wallets', 'transactions', 'disputes',
        'audit_logs', 'otp_verification', 'password_resets'
    ]
    
    try:
        db_name = os.getenv('MYSQL_DB', 'smart_farming')
        
        conn = MySQLdb.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            user=os.getenv('MYSQL_USER', 'root'),
            passwd=os.getenv('MYSQL_PASSWORD', ''),
            db=db_name,
            charset='utf8mb4'
        )
        
        cursor = conn.cursor()
        
        cursor.execute("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = %s", (db_name,))
        existing_tables = {row[0] for row in cursor.fetchall()}
        
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if missing_tables:
            print(f"✗ Missing tables: {', '.join(missing_tables)}")
            return False
        
        print(f"✓ All {len(required_tables)} tables created successfully")
        
        cursor.close()
        conn.close()
        
        return True
    
    except MySQLdb.Error as e:
        print(f"✗ Error verifying tables: {e}")
        return False

def print_completion():
    """Print completion message"""
    print("\n" + "="*60)
    print("INITIALIZATION COMPLETE")
    print("="*60)
    print("\n✓ Smart Farmer Marketplace database is ready!")
    print("\nNext steps:")
    print("1. Configure .env file with your settings")
    print("2. Run: python startup.py")
    print("3. Backend will be available at http://localhost:5000")
    print("\nDocumentation:")
    print("- API Endpoints: GET http://localhost:5000/api")
    print("- Health Check: GET http://localhost:5000/health")
    print("\n" + "="*60 + "\n")

def main():
    """Main initialization function"""
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║                                                                ║
    ║     SMART FARMER MARKETPLACE - Database Initialization        ║
    ║                                                                ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    # Run initialization steps
    steps = [
        ("Creating database", create_database),
        ("Importing schema", import_schema),
        ("Verifying tables", verify_tables),
        ("Creating admin user", create_admin_user)
    ]
    
    for step_name, step_func in steps:
        try:
            result = step_func()
            if not result:
                print(f"\n✗ Initialization failed at: {step_name}")
                sys.exit(1)
        except KeyboardInterrupt:
            print("\n\n✗ Initialization cancelled by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n✗ Error during {step_name}: {e}")
            sys.exit(1)
    
    print_completion()

if __name__ == '__main__':
    main()
