#!/usr/bin/env python3
"""
Admin Account Setup Script
Generates the password hash and SQL statement for creating the admin account
"""

from werkzeug.security import generate_password_hash

# Admin credentials
email = 'gundesandeep2005@gmail.com'
password = 'Sandy@7982'
name = 'Sandeep Gunde'
role = 'super_admin'

# Generate password hash
password_hash = generate_password_hash(password)

print("=" * 70)
print("ADMIN ACCOUNT SETUP")
print("=" * 70)
print()
print(f"Email: {email}")
print(f"Password: {password}")
print(f"Name: {name}")
print(f"Role: {role}")
print()
print("Password Hash (bcrypt):")
print(f"{password_hash}")
print()
print("=" * 70)
print("SQL INSERT STATEMENT:")
print("=" * 70)
print()

# Generate SQL insert statement
sql_statement = f"""INSERT INTO admins (email, password_hash, first_name, role, created_at) 
VALUES (
    '{email}',
    '{password_hash}',
    '{name}',
    '{role}',
    NOW()
);"""

print(sql_statement)
print()
print("=" * 70)
print("INSTRUCTIONS:")
print("=" * 70)
print()
print("1. Copy the SQL INSERT statement above")
print("2. Open MySQL Workbench or MySQL Command Line")
print("3. Select database: USE SmartFarmingDB;")
print("4. Paste and execute the INSERT statement")
print("5. Verify: SELECT * FROM admins WHERE email = 'gundesandeep2005@gmail.com';")
print()
print("Or run directly from command line:")
print("mysql -u root -p SmartFarmingDB -e \"<paste SQL here>\"")
print()
