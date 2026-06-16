"""
Comprehensive admin setup using Flask context
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from werkzeug.security import generate_password_hash
import MySQLdb

def setup_admin():
    with app.app_context():
        try:
            # Try using the Flask-MySQLdb connection
            from flask_mysqldb import MySQL
            from app import mysql
            
            cursor = mysql.connection.cursor()
            
            # Check if admins table exists
            cursor.execute("""
                SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'admins'
            """)
            
            table_exists = cursor.fetchone()
            
            if not table_exists:
                print("❌ admins table does not exist!")
                print("   Please load the database schema first:")
                print("   mysql -u root -p SmartFarmingDB < database/schema.sql")
                cursor.close()
                return False
            
            print("✅ admins table found")
            
            # Admin credentials
            email = 'gundesandeep2005@gmail.com'
            password = 'Sandy@7982'
            name = 'Sandeep Gunde'
            
            # Hash the password
            password_hash = generate_password_hash(password)
            
            # Check if admin already exists
            cursor.execute("SELECT * FROM admins WHERE email = %s", (email,))
            existing_admin = cursor.fetchone()
            
            if existing_admin:
                print(f"✅ Admin already exists!")
                print(f"   Email: {email}")
                print(f"   Admin ID: {existing_admin[0]}")
            else:
                # Create new admin
                cursor.execute(
                    """INSERT INTO admins (email, password_hash, name, role, created_at) 
                       VALUES (%s, %s, %s, %s, NOW())""",
                    (email, password_hash, name, 'super_admin')
                )
                mysql.connection.commit()
                
                print(f"✅ Admin created successfully!")
                print(f"   Email: {email}")
                print(f"   Password: {password}")
                print(f"   Name: {name}")
                print(f"   Role: super_admin")
                print(f"   Ready to login!")
            
            cursor.close()
            return True
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    print("🔧 Setting up admin account...")
    print()
    success = setup_admin()
    print()
    if success:
        print("✅ Setup complete!")
    else:
        print("❌ Setup failed!")
