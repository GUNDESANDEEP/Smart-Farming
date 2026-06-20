#!/usr/bin/env python3
"""
Fix Admin Login - Check and recreate admin user in PostgreSQL (Neon)
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', '')

if not DATABASE_URL:
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', '')
    db_name = os.getenv('DB_NAME', 'smartfarmingdb')
    DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# Admin credentials from .env
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'gundesandeep2005@gmail.com')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'Sandy@7981')

print("=" * 70)
print("ADMIN LOGIN FIX - PostgreSQL (Neon)")
print("=" * 70)
print(f"Database: {DATABASE_URL[:50]}...")
print(f"Admin Email: {ADMIN_EMAIL}")
print(f"Admin Password: {ADMIN_PASSWORD}")
print()

try:
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    print("[OK] Connected to PostgreSQL")
    print()

    # 1. Check if admins table exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'admins'
        )
    """)
    table_exists = cursor.fetchone()['exists']
    
    if not table_exists:
        print("[ERR] Table 'admins' does NOT exist! Creating it now...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                admin_id SERIAL PRIMARY KEY,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(500) NOT NULL,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50),
                role VARCHAR(50) DEFAULT 'moderator',
                permissions JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        conn.commit()
        print("[OK] Created admins table")
    else:
        print("[OK] Table 'admins' exists")
    
    # 2. Check table columns
    cursor.execute("""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns 
        WHERE table_name = 'admins'
        ORDER BY ordinal_position
    """)
    columns = cursor.fetchall()
    print(f"\nAdmins table columns:")
    for col in columns:
        max_len = f" ({col['character_maximum_length']})" if col['character_maximum_length'] else ""
        print(f"  - {col['column_name']}: {col['data_type']}{max_len}")
    
    # 3. Check existing admins
    cursor.execute("SELECT admin_id, email, first_name, last_name, role, is_active, password_hash FROM admins")
    admins = cursor.fetchall()
    
    print(f"\nExisting admins: {len(admins)}")
    for admin in admins:
        pw_match = check_password_hash(admin['password_hash'], ADMIN_PASSWORD)
        print(f"  - ID: {admin['admin_id']}, Email: {admin['email']}, "
              f"Name: {admin['first_name']} {admin.get('last_name', '') or ''}, "
              f"Role: {admin['role']}, Active: {admin['is_active']}, "
              f"Password matches '{ADMIN_PASSWORD}': {'YES' if pw_match else 'NO'}")
        
        if admin['email'] == ADMIN_EMAIL and not pw_match:
            # Try Sandy@7982 too
            pw_match_7982 = check_password_hash(admin['password_hash'], 'Sandy@7982')
            print(f"    Password matches 'Sandy@7982': {'YES' if pw_match_7982 else 'NO'}")
    
    # 4. Fix: Delete old admin and create with correct password
    if admins:
        # Check if our admin email exists
        cursor.execute("SELECT admin_id, password_hash FROM admins WHERE email = %s", (ADMIN_EMAIL,))
        existing = cursor.fetchone()
        
        if existing:
            pw_ok = check_password_hash(existing['password_hash'], ADMIN_PASSWORD)
            if pw_ok:
                print(f"\n[OK] Admin login should work! Email: {ADMIN_EMAIL}, Password: {ADMIN_PASSWORD}")
            else:
                print(f"\n[WARN] Admin exists but password doesn't match. Updating password...")
                new_hash = generate_password_hash(ADMIN_PASSWORD)
                cursor.execute(
                    "UPDATE admins SET password_hash = %s WHERE email = %s",
                    (new_hash, ADMIN_EMAIL)
                )
                conn.commit()
                print(f"[OK] Password updated! You can now login with:")
                print(f"   Email: {ADMIN_EMAIL}")
                print(f"   Password: {ADMIN_PASSWORD}")
        else:
            print(f"\n[WARN] No admin with email {ADMIN_EMAIL}. Creating one...")
            new_hash = generate_password_hash(ADMIN_PASSWORD)
            cursor.execute(
                """INSERT INTO admins (email, password_hash, first_name, last_name, role, is_active)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (ADMIN_EMAIL, new_hash, 'Sandeep', 'Gunde', 'super_admin', True)
            )
            conn.commit()
            print(f"[OK] Admin created! Login with:")
            print(f"   Email: {ADMIN_EMAIL}")
            print(f"   Password: {ADMIN_PASSWORD}")
    else:
        print(f"\n[WARN] No admins found. Creating admin user...")
        new_hash = generate_password_hash(ADMIN_PASSWORD)
        cursor.execute(
            """INSERT INTO admins (email, password_hash, first_name, last_name, role, is_active)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (ADMIN_EMAIL, new_hash, 'Sandeep', 'Gunde', 'super_admin', True)
        )
        conn.commit()
        print(f"[OK] Admin created! Login with:")
        print(f"   Email: {ADMIN_EMAIL}")
        print(f"   Password: {ADMIN_PASSWORD}")
    
    # 5. Verify the fix
    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)
    cursor.execute("SELECT admin_id, email, first_name, role, password_hash FROM admins WHERE email = %s", (ADMIN_EMAIL,))
    admin = cursor.fetchone()
    if admin:
        final_check = check_password_hash(admin['password_hash'], ADMIN_PASSWORD)
        print(f"Admin ID: {admin['admin_id']}")
        print(f"Email: {admin['email']}")
        print(f"Name: {admin['first_name']}")
        print(f"Role: {admin['role']}")
        print(f"Password '{ADMIN_PASSWORD}' works: {'YES' if final_check else 'NO'}")
        print(f"Password hash length: {len(admin['password_hash'])}")
    
    cursor.close()
    conn.close()
    print("\n[OK] Done!")

except Exception as e:
    print(f"\n[ERR] Error: {e}")
    import traceback
    traceback.print_exc()
