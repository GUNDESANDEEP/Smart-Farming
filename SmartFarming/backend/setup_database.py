"""
Database Setup Script for Smart Farming Backend
PostgreSQL version for Neon PostgreSQL.
Creates all required tables.
Run this once to set up the database.
"""

import psycopg2
import os
from dotenv import load_dotenv

# Load env from backend directory
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
# Also try parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

DATABASE_URL = os.getenv('DATABASE_URL', '')

if not DATABASE_URL:
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', '')
    db_name = os.getenv('DB_NAME', 'smartfarmingdb')
    DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    if db_host and 'neon.tech' in db_host:
        DATABASE_URL += "?sslmode=require"

def get_connection():
    """Get PostgreSQL connection"""
    return psycopg2.connect(DATABASE_URL)

TABLES = [
    # ==================== FARMERS ====================
    """
    CREATE TABLE IF NOT EXISTS farmers (
        id SERIAL PRIMARY KEY,
        phone VARCHAR(20) UNIQUE NOT NULL,
        email VARCHAR(255),
        password_hash VARCHAR(255) NOT NULL,
        first_name VARCHAR(100) NOT NULL,
        last_name VARCHAR(100) DEFAULT '',
        location VARCHAR(255),
        aadhar_number VARCHAR(20),
        land_area_hectares DECIMAL(10,2),
        crops_grown TEXT,
        experience_years INT,
        bank_account VARCHAR(50),
        bank_ifsc VARCHAR(20),
        bank_name VARCHAR(100),
        profile_image VARCHAR(500),
        latitude DECIMAL(10,6),
        longitude DECIMAL(10,6),
        is_verified BOOLEAN DEFAULT TRUE,
        is_active BOOLEAN DEFAULT TRUE,
        user_id INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_farmers_phone ON farmers(phone);",
    "CREATE INDEX IF NOT EXISTS idx_farmers_email ON farmers(email);",

    # ==================== BUYERS ====================
    """
    CREATE TABLE IF NOT EXISTS buyers (
        id SERIAL PRIMARY KEY,
        buyer_id INT UNIQUE,
        phone VARCHAR(20) UNIQUE NOT NULL,
        email VARCHAR(255),
        password_hash VARCHAR(255) NOT NULL,
        first_name VARCHAR(100) NOT NULL,
        last_name VARCHAR(100) DEFAULT '',
        location VARCHAR(255),
        city VARCHAR(100),
        state VARCHAR(100),
        pincode VARCHAR(10),
        address TEXT,
        profile_image VARCHAR(500),
        is_verified BOOLEAN DEFAULT TRUE,
        user_id INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_buyers_phone ON buyers(phone);",
    "CREATE INDEX IF NOT EXISTS idx_buyers_email ON buyers(email);",

    # ==================== PRODUCTS ====================
    """
    CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY,
        farmer_id INT NOT NULL REFERENCES farmers(id) ON DELETE CASCADE,
        name VARCHAR(255) NOT NULL,
        slug VARCHAR(300),
        description TEXT,
        detailed_description TEXT,
        category VARCHAR(100),
        quantity DECIMAL(12,2) DEFAULT 0,
        price DECIMAL(10,2) NOT NULL,
        unit VARCHAR(20) DEFAULT 'kg',
        min_order_quantity DECIMAL(12,2),
        max_order_quantity DECIMAL(12,2),
        discount_percentage DECIMAL(5,2) DEFAULT 0,
        harvest_date DATE,
        expiry_date DATE,
        location VARCHAR(255),
        images JSONB,
        specifications JSONB,
        certifications TEXT,
        is_available BOOLEAN DEFAULT TRUE,
        is_organic BOOLEAN DEFAULT FALSE,
        status VARCHAR(20) DEFAULT 'approved' CHECK (status IN ('pending','approved','rejected','discontinued')),
        average_rating DECIMAL(3,2) DEFAULT 0,
        total_reviews INT DEFAULT 0,
        views_count INT DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_products_farmer ON products(farmer_id);",
    "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);",
    "CREATE INDEX IF NOT EXISTS idx_products_available ON products(is_available);",

    # ==================== ORDERS ====================
    """
    CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY,
        order_number VARCHAR(50) UNIQUE,
        buyer_id INT NOT NULL REFERENCES buyers(id) ON DELETE CASCADE,
        farmer_id INT NOT NULL REFERENCES farmers(id) ON DELETE CASCADE,
        product_id INT REFERENCES products(id),
        quantity DECIMAL(12,2),
        total_amount DECIMAL(12,2),
        status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending','confirmed','packed','shipped','delivered','cancelled','returned')),
        payment_method VARCHAR(50),
        payment_status VARCHAR(20) DEFAULT 'pending' CHECK (payment_status IN ('pending','completed','failed','refunded')),
        delivery_address TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_orders_buyer ON orders(buyer_id);",
    "CREATE INDEX IF NOT EXISTS idx_orders_farmer ON orders(farmer_id);",
    "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);",

    # ==================== WALLET ====================
    """
    CREATE TABLE IF NOT EXISTS wallet (
        id SERIAL PRIMARY KEY,
        farmer_id INT NOT NULL UNIQUE REFERENCES farmers(id) ON DELETE CASCADE,
        balance DECIMAL(12,2) DEFAULT 0,
        total_earnings DECIMAL(12,2) DEFAULT 0,
        total_withdrawn DECIMAL(12,2) DEFAULT 0,
        withdrawal_pending DECIMAL(12,2) DEFAULT 0,
        last_withdrawal_date TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,

    # ==================== OTP VERIFICATION ====================
    """
    CREATE TABLE IF NOT EXISTS otp_verification (
        id SERIAL PRIMARY KEY,
        phone VARCHAR(20) NOT NULL,
        otp VARCHAR(10) NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_otp_verification_phone ON otp_verification(phone);",

    # ==================== CART ====================
    """
    CREATE TABLE IF NOT EXISTS cart (
        id SERIAL PRIMARY KEY,
        buyer_id INT NOT NULL REFERENCES buyers(id) ON DELETE CASCADE,
        product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
        quantity DECIMAL(12,2) DEFAULT 1,
        price DECIMAL(10,2),
        is_active BOOLEAN DEFAULT TRUE,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(buyer_id, product_id)
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_cart_buyer ON cart(buyer_id);",

    # ==================== PAYMENTS ====================
    """
    CREATE TABLE IF NOT EXISTS payments (
        id SERIAL PRIMARY KEY,
        payment_id INT UNIQUE,
        order_id INT DEFAULT NULL,
        buyer_id INT,
        amount DECIMAL(12,2) NOT NULL,
        payment_method VARCHAR(50) DEFAULT 'razorpay',
        status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending','completed','failed','refunded')),
        transaction_id VARCHAR(100),
        razorpay_payment_id VARCHAR(100),
        razorpay_order_id VARCHAR(100),
        razorpay_signature VARCHAR(255),
        error_message TEXT,
        payment_date TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_payments_order ON payments(order_id);",
    "CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);",

    # ==================== BUYER REVIEWS ====================
    """
    CREATE TABLE IF NOT EXISTS buyer_reviews (
        id SERIAL PRIMARY KEY,
        order_id INT NOT NULL REFERENCES orders(id),
        buyer_id INT NOT NULL REFERENCES buyers(id),
        product_id INT NOT NULL REFERENCES products(id),
        farmer_id INT NOT NULL REFERENCES farmers(id),
        product_rating INT DEFAULT 5,
        product_review TEXT,
        farmer_rating INT DEFAULT 5,
        farmer_review TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_buyer_reviews_product ON buyer_reviews(product_id);",
    "CREATE INDEX IF NOT EXISTS idx_buyer_reviews_farmer ON buyer_reviews(farmer_id);",

    # ==================== BUYER ADDRESSES ====================
    """
    CREATE TABLE IF NOT EXISTS buyer_addresses (
        id SERIAL PRIMARY KEY,
        buyer_id INT NOT NULL REFERENCES buyers(id) ON DELETE CASCADE,
        type VARCHAR(50) DEFAULT 'home',
        address TEXT,
        city VARCHAR(100),
        state VARCHAR(100),
        pincode VARCHAR(10),
        is_default BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_buyer_addresses_buyer ON buyer_addresses(buyer_id);",

    # ==================== ADMIN ACTIVITY LOG ====================
    """
    CREATE TABLE IF NOT EXISTS admin_activity_log (
        id SERIAL PRIMARY KEY,
        admin_id INT NOT NULL,
        action VARCHAR(100) NOT NULL,
        module VARCHAR(50),
        target_id INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_admin_activity_admin ON admin_activity_log(admin_id);",

    # ==================== ADMINS ====================
    """
    CREATE TABLE IF NOT EXISTS admins (
        admin_id SERIAL PRIMARY KEY,
        email VARCHAR(100) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        first_name VARCHAR(50) NOT NULL,
        last_name VARCHAR(50),
        role VARCHAR(20) DEFAULT 'moderator' CHECK (role IN ('super_admin','moderator','analyst')),
        permissions JSONB,
        user_id INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_admins_role ON admins(role);",
    "CREATE INDEX IF NOT EXISTS idx_admins_active ON admins(is_active);",

    # ==================== ORDER TRACKING ====================
    """
    CREATE TABLE IF NOT EXISTS order_tracking (
        id SERIAL PRIMARY KEY,
        order_id INT NOT NULL REFERENCES orders(id),
        status VARCHAR(50) NOT NULL,
        location VARCHAR(255),
        latitude DECIMAL(10,8),
        longitude DECIMAL(11,8),
        description TEXT,
        updated_by VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,

    # ==================== RETURN REQUESTS ====================
    """
    CREATE TABLE IF NOT EXISTS return_requests (
        id SERIAL PRIMARY KEY,
        order_id INT NOT NULL REFERENCES orders(id),
        buyer_id INT NOT NULL REFERENCES buyers(id),
        reason TEXT NOT NULL,
        status VARCHAR(20) DEFAULT 'requested' CHECK (status IN ('requested','approved','rejected','completed')),
        admin_notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,

    # ==================== DISPUTES ====================
    """
    CREATE TABLE IF NOT EXISTS disputes (
        id SERIAL PRIMARY KEY,
        order_id INT NOT NULL REFERENCES orders(id),
        raised_by VARCHAR(50) NOT NULL,
        raised_by_id INT NOT NULL,
        type VARCHAR(50),
        description TEXT NOT NULL,
        status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open','investigating','resolved','closed')),
        resolution TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,

    # ==================== AI LOGS ====================
    """
    CREATE TABLE IF NOT EXISTS ai_logs (
        id SERIAL PRIMARY KEY,
        user_id INT,
        user_type VARCHAR(20),
        feature VARCHAR(50) NOT NULL,
        input_data JSONB,
        output_data JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,

    # ==================== REVIEW REPORTS ====================
    """
    CREATE TABLE IF NOT EXISTS review_reports (
        id SERIAL PRIMARY KEY,
        review_id INT NOT NULL REFERENCES buyer_reviews(id),
        reported_by INT NOT NULL,
        reason TEXT NOT NULL,
        status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending','reviewed','dismissed')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,

    # ==================== OTPs (for email/login OTP verification) ====================
    """
    CREATE TABLE IF NOT EXISTS otps (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255),
        phone VARCHAR(20),
        otp VARCHAR(10) NOT NULL,
        purpose VARCHAR(50) DEFAULT 'verification',
        is_verified BOOLEAN DEFAULT FALSE,
        attempts INT DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_otps_email ON otps(email);",
    "CREATE INDEX IF NOT EXISTS idx_otps_phone ON otps(phone);",

    # ==================== PAYMENT OTPs ====================
    """
    CREATE TABLE IF NOT EXISTS payment_otps (
        id SERIAL PRIMARY KEY,
        buyer_id INT,
        buyer_phone VARCHAR(20),
        buyer_email VARCHAR(255),
        otp VARCHAR(10) NOT NULL,
        amount DECIMAL(12,2),
        product_details JSONB,
        farmer_id INT,
        status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending','verified','expired')),
        verified_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_payment_otps_otp ON payment_otps(otp);",
    "CREATE INDEX IF NOT EXISTS idx_payment_otps_status ON payment_otps(status);",

    # ==================== RECEIPTS ====================
    """
    CREATE TABLE IF NOT EXISTS receipts (
        id SERIAL PRIMARY KEY,
        receipt_id VARCHAR(50) UNIQUE NOT NULL,
        payment_id INT,
        buyer_id INT,
        farmer_id INT,
        subtotal DECIMAL(12,2) DEFAULT 0,
        discount DECIMAL(12,2) DEFAULT 0,
        grand_total DECIMAL(12,2) DEFAULT 0,
        payment_type VARCHAR(50),
        payment_status VARCHAR(50) DEFAULT 'completed',
        buyer_name VARCHAR(200),
        buyer_phone VARCHAR(20),
        buyer_email VARCHAR(255),
        qr_code VARCHAR(500),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_receipts_receipt_id ON receipts(receipt_id);",
    "CREATE INDEX IF NOT EXISTS idx_receipts_farmer ON receipts(farmer_id);",
    "CREATE INDEX IF NOT EXISTS idx_receipts_buyer ON receipts(buyer_id);",

    # ==================== RECEIPT ITEMS ====================
    """
    CREATE TABLE IF NOT EXISTS receipt_items (
        id SERIAL PRIMARY KEY,
        receipt_id INT NOT NULL REFERENCES receipts(id) ON DELETE CASCADE,
        product_id INT,
        product_name VARCHAR(255),
        quantity_kg DECIMAL(12,2) DEFAULT 0,
        price_per_kg DECIMAL(10,2) DEFAULT 0,
        product_quality VARCHAR(50) DEFAULT 'Standard',
        item_total DECIMAL(12,2) DEFAULT 0
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_receipt_items_receipt ON receipt_items(receipt_id);",

    # ==================== TRANSACTIONS ====================
    """
    CREATE TABLE IF NOT EXISTS transactions (
        id SERIAL PRIMARY KEY,
        transaction_id VARCHAR(100) UNIQUE,
        payment_id INT,
        receipt_id INT,
        user_id INT,
        user_type VARCHAR(20),
        type VARCHAR(10) NOT NULL CHECK (type IN ('credit','debit')),
        amount DECIMAL(12,2) NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_transactions_tid ON transactions(transaction_id);",
    "CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id, user_type);",

    # ==================== CONVERSATIONS ====================
    """
    CREATE TABLE IF NOT EXISTS conversations (
        id SERIAL PRIMARY KEY,
        user_1_id INT NOT NULL,
        user_2_id INT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_1_id, user_2_id)
    );
    """,

    # ==================== MESSAGES ====================
    """
    CREATE TABLE IF NOT EXISTS messages (
        id SERIAL PRIMARY KEY,
        conversation_id INT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
        sender_id INT NOT NULL,
        receiver_id INT NOT NULL,
        content TEXT,
        attachment_url VARCHAR(500),
        is_read BOOLEAN DEFAULT FALSE,
        read_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,

    # ==================== NOTIFICATIONS ====================
    """
    CREATE TABLE IF NOT EXISTS notifications (
        id SERIAL PRIMARY KEY,
        user_id INT NOT NULL,
        title VARCHAR(255),
        message TEXT,
        type VARCHAR(50),
        data JSONB,
        action_url VARCHAR(500),
        is_read BOOLEAN DEFAULT FALSE,
        read_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,

    # ==================== USERS (if auth routes use it) ====================
    """
    CREATE TABLE IF NOT EXISTS roles (
        id SERIAL PRIMARY KEY,
        name VARCHAR(50) UNIQUE NOT NULL
    );
    """,
    """
    INSERT INTO roles (name) VALUES ('farmer'), ('buyer'), ('admin')
    ON CONFLICT (name) DO NOTHING;
    """,
    """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(100),
        email VARCHAR(255),
        phone VARCHAR(20),
        password_hash VARCHAR(255),
        first_name VARCHAR(100),
        last_name VARCHAR(100),
        profile_image VARCHAR(500),
        role_id INT REFERENCES roles(id),
        firebase_uid VARCHAR(255),
        status VARCHAR(20) DEFAULT 'active',
        is_verified BOOLEAN DEFAULT FALSE,
        email_verified_at TIMESTAMP,
        phone_verified_at TIMESTAMP,
        last_login TIMESTAMP,
        two_factor_enabled BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
]

# ==================== AUTO-UPDATE updated_at FUNCTION ====================
UPDATE_TRIGGER_FUNC = """
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

UPDATE_TRIGGER_TABLES = [
    'farmers', 'buyers', 'products', 'orders', 'wallet', 'payments',
    'return_requests', 'disputes', 'admins', 'conversations'
]


def setup_database():
    """Create all required tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    print(f"Connected to PostgreSQL (Neon)")
    print(f"Database URL: {DATABASE_URL[:50]}...")
    print("=" * 60)
    
    success_count = 0
    error_count = 0
    
    for i, sql in enumerate(TABLES):
        try:
            cursor.execute(sql)
            conn.commit()
            # Extract table name from SQL
            table_name = "statement"
            sql_upper = sql.strip().upper()
            if "CREATE TABLE" in sql_upper:
                parts = sql.strip().split()
                for j, part in enumerate(parts):
                    if part.upper() == 'EXISTS' and j + 1 < len(parts):
                        table_name = parts[j + 1].strip('(').strip()
                        break
            elif "CREATE INDEX" in sql_upper:
                table_name = "index"
            elif "INSERT" in sql_upper:
                table_name = "seed data"
                        
            print(f"  [OK] [{i+1}] Created/verified: {table_name}")
            success_count += 1
        except Exception as e:
            conn.rollback()
            error_msg = str(e)
            if 'already exists' in error_msg.lower():
                print(f"  [SKIP] [{i+1}] Already exists (OK)")
                success_count += 1
            else:
                print(f"  [ERR] [{i+1}] Error: {error_msg}")
                error_count += 1
    
    # Create updated_at trigger function
    print("\n-- Creating auto-update trigger function --")
    try:
        cursor.execute(UPDATE_TRIGGER_FUNC)
        conn.commit()
        print("  [OK] update_updated_at_column() function created")
    except Exception as e:
        conn.rollback()
        print(f"  [WARN] Trigger function: {e}")
    
    # Apply trigger to tables
    for table in UPDATE_TRIGGER_TABLES:
        try:
            trigger_name = f"set_updated_at_{table}"
            cursor.execute(f"""
                DO $$ BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_trigger WHERE tgname = '{trigger_name}'
                    ) THEN
                        CREATE TRIGGER {trigger_name}
                        BEFORE UPDATE ON {table}
                        FOR EACH ROW
                        EXECUTE FUNCTION update_updated_at_column();
                    END IF;
                END $$;
            """)
            conn.commit()
            print(f"  [OK] Trigger on {table}")
        except Exception as e:
            conn.rollback()
            print(f"  [WARN] Trigger on {table}: {e}")
    
    # Auto-fill buyer_id = id
    print("\n-- Setting up buyer_id auto-fill --")
    try:
        cursor.execute("""
            UPDATE buyers SET buyer_id = id WHERE buyer_id IS NULL;
        """)
        conn.commit()
        print("  [OK] buyer_id backfilled")
    except Exception as e:
        conn.rollback()
        print(f"  [WARN] buyer_id backfill: {e}")
    
    # Verify tables exist
    print("\n" + "=" * 60)
    print("Verifying tables...")
    cursor.execute("""
        SELECT tablename FROM pg_tables 
        WHERE schemaname = 'public'
        ORDER BY tablename
    """)
    tables = cursor.fetchall()
    print(f"\nTables in database:")
    for t in tables:
        print(f"   - {t[0]}")
    
    cursor.close()
    conn.close()
    
    print(f"\n{'=' * 60}")
    print(f"Setup complete: {success_count} succeeded, {error_count} failed")
    
    return error_count == 0


if __name__ == '__main__':
    print(">> Smart Farming Database Setup (PostgreSQL)")
    print("=" * 60)
    setup_database()
