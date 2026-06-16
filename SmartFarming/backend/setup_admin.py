"""
Direct admin creation using SQL insert
"""
import MySQLdb
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Database credentials from .env
db_host = os.getenv('DB_HOST', 'localhost')
db_user = os.getenv('DB_USER', 'root')
db_password = os.getenv('DB_PASSWORD', '')
db_name = os.getenv('DB_NAME', 'SmartFarmingDB')

print(f"📊 Database Connection:")
print(f"   Host: {db_host}")
print(f"   User: {db_user}")
print(f"   Database: {db_name}")
print()

try:
    # Connect to database
    connection = MySQLdb.connect(
        host=db_host,
        user=db_user,
        passwd=db_password,
        db=db_name
    )
    cursor = connection.cursor()
    print("✅ Connected to database successfully!")
    print()
    
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
        print(f"   Name: {existing_admin[3]}")
        print(f"   Role: {existing_admin[4]}")
    else:
        # Create new admin
        cursor.execute(
            "INSERT INTO admins (email, password_hash, name, role, created_at) VALUES (%s, %s, %s, %s, NOW())",
            (email, password_hash, name, 'super_admin')
        )
        connection.commit()
        
        print(f"✅ Admin created successfully!")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
        print(f"   Name: {name}")
        print(f"   Role: super_admin")
        print(f"   Admin ID: {cursor.lastrowid}")
    
    print()
    print("🎉 Admin account setup complete!")
    
    cursor.close()
    connection.close()
    
except MySQLdb.Error as e:
    print(f"❌ MySQL Error: {e}")
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
