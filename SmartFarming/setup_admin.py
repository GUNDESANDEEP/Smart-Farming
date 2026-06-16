#!/usr/bin/env python3
import pymysql
from werkzeug.security import generate_password_hash

# Database connection
connection = pymysql.connect(
    host='127.0.0.1',
    user='root',
    password='sandeep@7981',
    database='SmartFarmingDB'
)

cursor = connection.cursor()

# Create admin table
admin_table_sql = """
CREATE TABLE IF NOT EXISTS admins (
  admin_id INT PRIMARY KEY AUTO_INCREMENT,
  email VARCHAR(100) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  first_name VARCHAR(50) NOT NULL,
  last_name VARCHAR(50),
  role ENUM('super_admin', 'moderator', 'analyst') DEFAULT 'moderator',
  permissions JSON,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  last_login DATETIME,
  is_active BOOLEAN DEFAULT TRUE,
  INDEX idx_email (email),
  INDEX idx_role (role),
  INDEX idx_active (is_active)
)
"""

try:
    print("Creating admin table...")
    cursor.execute(admin_table_sql)
    print("✓ Admin table created successfully")
except Exception as e:
    print(f"⚠️  Admin table already exists or error: {e}")

# Create admin user
email = 'gundesandeep2005@gmail.com'
password = 'Sandy@7981'
password_hash = generate_password_hash(password)

insert_admin_sql = """
INSERT IGNORE INTO admins (email, password_hash, first_name, last_name, role, is_active)
VALUES (%s, %s, %s, %s, %s, %s)
"""

try:
    print(f"Creating admin user: {email}")
    cursor.execute(insert_admin_sql, (email, password_hash, 'Sandeep', 'Gunde', 'super_admin', True))
    connection.commit()
    print(f"✓ Admin user created successfully")
    print(f"  Email: {email}")
    print(f"  Password: {password}")
except Exception as e:
    print(f"⚠️  Admin user already exists or error: {e}")
    connection.rollback()

# Verify
cursor.execute("SELECT admin_id, email, role FROM admins WHERE email = %s", (email,))
result = cursor.fetchone()

if result:
    print(f"\n✓ Verified admin user:")
    print(f"  Admin ID: {result[0]}")
    print(f"  Email: {result[1]}")
    print(f"  Role: {result[2]}")
else:
    print("❌ Admin user not found")

cursor.close()
connection.close()
