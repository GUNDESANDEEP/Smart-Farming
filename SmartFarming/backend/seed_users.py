"""
Seed default users for SmartFarming
Run once after setup_database.py to create test accounts.
"""

import psycopg2
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

DATABASE_URL = os.getenv('DATABASE_URL', '')

if not DATABASE_URL:
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', '')
    db_name = os.getenv('DB_NAME', 'smartfarmingdb')
    DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


def seed_users():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    admin_email = os.getenv('ADMIN_EMAIL', 'gundesandeep2005@gmail.com')
    admin_password = os.getenv('ADMIN_PASSWORD', 'Sandy@7981')

    print("=" * 60)
    print("  Seeding default users...")
    print("=" * 60)

    # ── 1. Admin ──
    try:
        cursor.execute("SELECT admin_id FROM admins WHERE email = %s", (admin_email,))
        if not cursor.fetchone():
            password_hash = generate_password_hash(admin_password)
            cursor.execute(
                """INSERT INTO admins (email, password_hash, first_name, last_name, role)
                   VALUES (%s, %s, %s, %s, %s)""",
                (admin_email, password_hash, 'Sandeep', 'Gunde', 'super_admin')
            )
            conn.commit()
            print(f"  [OK] Admin created: {admin_email} / {admin_password}")
        else:
            print(f"  [SKIP] Admin already exists: {admin_email}")
    except Exception as e:
        conn.rollback()
        print(f"  [ERR] Admin: {e}")

    # ── 2. Default Farmer ──
    farmer_email = 'farmer@smartfarm.com'
    farmer_phone = '9876543210'
    farmer_password = 'Farmer@123'
    try:
        cursor.execute("SELECT id FROM farmers WHERE email = %s", (farmer_email,))
        if not cursor.fetchone():
            password_hash = generate_password_hash(farmer_password)
            cursor.execute(
                """INSERT INTO farmers (first_name, last_name, email, phone, password_hash, location)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                ('Demo', 'Farmer', farmer_email, farmer_phone, password_hash, 'Hyderabad')
            )
            conn.commit()
            # Create wallet for farmer
            cursor.execute("SELECT id FROM farmers WHERE email = %s", (farmer_email,))
            fid = cursor.fetchone()[0]
            try:
                cursor.execute(
                    "INSERT INTO wallet (farmer_id, balance, total_earnings) VALUES (%s, 0, 0)", (fid,)
                )
                conn.commit()
            except Exception:
                conn.rollback()
            print(f"  [OK] Farmer created: {farmer_email} / {farmer_password}")
        else:
            print(f"  [SKIP] Farmer already exists: {farmer_email}")
    except Exception as e:
        conn.rollback()
        print(f"  [ERR] Farmer: {e}")

    # ── 3. Default Buyer (phone: 9347538630) ──
    buyer_phone = '9347538630'
    buyer_email = 'buyer@smartfarm.com'
    buyer_password = 'Buyer@123'
    try:
        cursor.execute("SELECT id FROM buyers WHERE phone = %s", (buyer_phone,))
        if not cursor.fetchone():
            password_hash = generate_password_hash(buyer_password)
            cursor.execute(
                """INSERT INTO buyers (first_name, last_name, email, phone, password_hash, location)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                ('Sandeep', 'Gunde', buyer_email, buyer_phone, password_hash, 'Hyderabad')
            )
            conn.commit()
            # Set buyer_id = id
            cursor.execute("UPDATE buyers SET buyer_id = id WHERE phone = %s AND buyer_id IS NULL", (buyer_phone,))
            conn.commit()
            print(f"  [OK] Buyer created: phone={buyer_phone} / password={buyer_password}")
        else:
            print(f"  [SKIP] Buyer already exists: phone={buyer_phone}")
    except Exception as e:
        conn.rollback()
        print(f"  [ERR] Buyer: {e}")

    cursor.close()
    conn.close()

    print("\n" + "=" * 60)
    print("  Default Login Credentials:")
    print("=" * 60)
    print(f"  Admin:  {admin_email} / {admin_password}")
    print(f"  Farmer: {farmer_email} / {farmer_password}")
    print(f"  Buyer:  phone={buyer_phone} / password={buyer_password}")
    print("=" * 60)


if __name__ == '__main__':
    seed_users()
