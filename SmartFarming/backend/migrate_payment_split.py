"""
Migration: Add payment split columns to orders table
and create platform_earnings table for admin revenue tracking.
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

DATABASE_URL = os.getenv('DATABASE_URL', '')
if not DATABASE_URL:
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', '')
    db_name = os.getenv('DB_NAME', 'smartfarmingdb')
    DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

migrations = [
    # 1. Add split columns to orders table
    "ALTER TABLE orders ADD COLUMN IF NOT EXISTS gst_amount DECIMAL(12,2) DEFAULT 0;",
    "ALTER TABLE orders ADD COLUMN IF NOT EXISTS platform_fee DECIMAL(12,2) DEFAULT 0;",
    "ALTER TABLE orders ADD COLUMN IF NOT EXISTS farmer_payout DECIMAL(12,2) DEFAULT 0;",
    
    # 2. Create platform_earnings table to track admin revenue
    """
    CREATE TABLE IF NOT EXISTS platform_earnings (
        id SERIAL PRIMARY KEY,
        order_id INT REFERENCES orders(id),
        order_number VARCHAR(50),
        farmer_id INT REFERENCES farmers(id),
        buyer_id INT REFERENCES buyers(id),
        total_amount DECIMAL(12,2) NOT NULL DEFAULT 0,
        gst_amount DECIMAL(12,2) NOT NULL DEFAULT 0,
        platform_fee DECIMAL(12,2) NOT NULL DEFAULT 0,
        farmer_payout DECIMAL(12,2) NOT NULL DEFAULT 0,
        gst_rate DECIMAL(5,2) DEFAULT 1.00,
        platform_fee_rate DECIMAL(5,2) DEFAULT 2.00,
        settlement_status VARCHAR(20) DEFAULT 'pending' CHECK (settlement_status IN ('pending','settled','failed')),
        settled_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_platform_earnings_order ON platform_earnings(order_id);",
    "CREATE INDEX IF NOT EXISTS idx_platform_earnings_farmer ON platform_earnings(farmer_id);",
    "CREATE INDEX IF NOT EXISTS idx_platform_earnings_status ON platform_earnings(settlement_status);",
    
    # 3. Add delivery_otp columns (needed for order flow)
    "ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_otp VARCHAR(10);",
    "ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_otp_sent_at TIMESTAMP;",
    
    # 4. Update status constraint to include new statuses
    """
    DO $$ BEGIN
        ALTER TABLE orders DROP CONSTRAINT IF EXISTS orders_status_check;
        ALTER TABLE orders ADD CONSTRAINT orders_status_check 
            CHECK (status IN ('pending','confirmed','processing','packed','dispatched','in_transit','out_for_delivery','delivered','cancelled','returned','return_requested'));
    EXCEPTION WHEN others THEN NULL;
    END $$;
    """,
    
    # 5. Update payment_status constraint
    """
    DO $$ BEGIN
        ALTER TABLE orders DROP CONSTRAINT IF EXISTS orders_payment_status_check;
        ALTER TABLE orders ADD CONSTRAINT orders_payment_status_check 
            CHECK (payment_status IN ('pending','completed','failed','refunded','cod_pending'));
    EXCEPTION WHEN others THEN NULL;
    END $$;
    """,
]

print("Running payment split migration...")
print("=" * 60)

for i, sql in enumerate(migrations):
    try:
        cursor.execute(sql)
        conn.commit()
        print(f"  [OK] Migration {i+1} applied")
    except Exception as e:
        conn.rollback()
        err = str(e)
        if 'already exists' in err.lower():
            print(f"  [SKIP] Migration {i+1} already applied")
        else:
            print(f"  [ERR] Migration {i+1}: {err}")

cursor.close()
conn.close()
print("\n[DONE] Payment split migration complete!")
