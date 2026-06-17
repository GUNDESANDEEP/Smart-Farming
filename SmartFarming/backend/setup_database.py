"""
Database Setup Script for Smart Farming Backend
Creates all required tables matching the actual backend code expectations.
Run this once to set up the database.
"""

import MySQLdb
import os
from dotenv import load_dotenv

# Load env from backend directory
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
# Also try parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'SmartFarmingDB')

def get_connection():
    """Get MySQL connection"""
    return MySQLdb.connect(
        host=DB_HOST,
        user=DB_USER,
        passwd=DB_PASSWORD,
        db=DB_NAME
    )

TABLES = [
    # ==================== FARMERS ====================
    """
    CREATE TABLE IF NOT EXISTS farmers (
        id INT PRIMARY KEY AUTO_INCREMENT,
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_phone (phone),
        INDEX idx_email (email)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # ==================== BUYERS ====================
    """
    CREATE TABLE IF NOT EXISTS buyers (
        id INT PRIMARY KEY AUTO_INCREMENT,
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_phone (phone),
        INDEX idx_email (email)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # Auto-fill buyer_id = id with a trigger
    """
    CREATE TRIGGER IF NOT EXISTS set_buyer_id
    BEFORE INSERT ON buyers
    FOR EACH ROW
    BEGIN
        IF NEW.buyer_id IS NULL THEN
            SET NEW.buyer_id = NULL;
        END IF;
    END;
    """,

    # ==================== PRODUCTS ====================
    """
    CREATE TABLE IF NOT EXISTS products (
        id INT PRIMARY KEY AUTO_INCREMENT,
        farmer_id INT NOT NULL,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        category VARCHAR(100),
        quantity DECIMAL(12,2) DEFAULT 0,
        price DECIMAL(10,2) NOT NULL,
        unit VARCHAR(20) DEFAULT 'kg',
        harvest_date DATE,
        location VARCHAR(255),
        images JSON,
        is_available BOOLEAN DEFAULT TRUE,
        status ENUM('pending','approved','rejected','discontinued') DEFAULT 'approved',
        organic BOOLEAN DEFAULT FALSE,
        average_rating DECIMAL(3,2) DEFAULT 0,
        total_reviews INT DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE CASCADE,
        INDEX idx_farmer (farmer_id),
        INDEX idx_category (category),
        INDEX idx_available (is_available)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # ==================== ORDERS ====================
    """
    CREATE TABLE IF NOT EXISTS orders (
        id INT PRIMARY KEY AUTO_INCREMENT,
        order_number VARCHAR(50) UNIQUE,
        buyer_id INT NOT NULL,
        farmer_id INT NOT NULL,
        product_id INT,
        quantity DECIMAL(12,2),
        total_amount DECIMAL(12,2),
        status ENUM('pending','confirmed','packed','shipped','delivered','cancelled','returned') DEFAULT 'pending',
        payment_method VARCHAR(50),
        payment_status ENUM('pending','completed','failed','refunded') DEFAULT 'pending',
        delivery_address TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (buyer_id) REFERENCES buyers(id) ON DELETE CASCADE,
        FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE CASCADE,
        INDEX idx_buyer (buyer_id),
        INDEX idx_farmer (farmer_id),
        INDEX idx_status (status)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # ==================== WALLET ====================
    """
    CREATE TABLE IF NOT EXISTS wallet (
        id INT PRIMARY KEY AUTO_INCREMENT,
        farmer_id INT NOT NULL UNIQUE,
        balance DECIMAL(12,2) DEFAULT 0,
        total_earnings DECIMAL(12,2) DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # ==================== OTP VERIFICATION ====================
    """
    CREATE TABLE IF NOT EXISTS otp_verification (
        id INT PRIMARY KEY AUTO_INCREMENT,
        phone VARCHAR(20) NOT NULL,
        otp VARCHAR(10) NOT NULL,
        expires_at DATETIME NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_phone (phone)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # ==================== CART ====================
    """
    CREATE TABLE IF NOT EXISTS cart (
        id INT PRIMARY KEY AUTO_INCREMENT,
        buyer_id INT NOT NULL,
        product_id INT NOT NULL,
        quantity DECIMAL(12,2) DEFAULT 1,
        price DECIMAL(10,2),
        is_active BOOLEAN DEFAULT TRUE,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (buyer_id) REFERENCES buyers(id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
        INDEX idx_buyer (buyer_id),
        UNIQUE KEY unique_buyer_product (buyer_id, product_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # ==================== PAYMENTS ====================
    """
    CREATE TABLE IF NOT EXISTS payments (
        id INT PRIMARY KEY AUTO_INCREMENT,
        payment_id INT UNIQUE,
        order_id INT DEFAULT NULL,
        buyer_id INT,
        amount DECIMAL(12,2) NOT NULL,
        payment_method VARCHAR(50) DEFAULT 'razorpay',
        status ENUM('pending','completed','failed','refunded') DEFAULT 'pending',
        transaction_id VARCHAR(100),
        razorpay_payment_id VARCHAR(100),
        razorpay_order_id VARCHAR(100),
        razorpay_signature VARCHAR(255),
        error_message TEXT,
        payment_date TIMESTAMP NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_order (order_id),
        INDEX idx_status (status)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # ==================== BUYER REVIEWS ====================
    """
    CREATE TABLE IF NOT EXISTS buyer_reviews (
        id INT PRIMARY KEY AUTO_INCREMENT,
        order_id INT NOT NULL,
        buyer_id INT NOT NULL,
        product_id INT NOT NULL,
        farmer_id INT NOT NULL,
        product_rating INT DEFAULT 5,
        product_review TEXT,
        farmer_rating INT DEFAULT 5,
        farmer_review TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (order_id) REFERENCES orders(id),
        FOREIGN KEY (buyer_id) REFERENCES buyers(id),
        FOREIGN KEY (product_id) REFERENCES products(id),
        FOREIGN KEY (farmer_id) REFERENCES farmers(id),
        INDEX idx_product (product_id),
        INDEX idx_farmer (farmer_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # ==================== BUYER ADDRESSES ====================
    """
    CREATE TABLE IF NOT EXISTS buyer_addresses (
        id INT PRIMARY KEY AUTO_INCREMENT,
        buyer_id INT NOT NULL,
        type VARCHAR(50) DEFAULT 'home',
        address TEXT,
        city VARCHAR(100),
        state VARCHAR(100),
        pincode VARCHAR(10),
        is_default BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (buyer_id) REFERENCES buyers(id) ON DELETE CASCADE,
        INDEX idx_buyer (buyer_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # ==================== ADMIN ACTIVITY LOG ====================
    """
    CREATE TABLE IF NOT EXISTS admin_activity_log (
        id INT PRIMARY KEY AUTO_INCREMENT,
        admin_id INT NOT NULL,
        action VARCHAR(100) NOT NULL,
        module VARCHAR(50),
        target_id INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_admin (admin_id),
        INDEX idx_action (action)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # ==================== ADMINS (if not exists) ====================
    """
    CREATE TABLE IF NOT EXISTS admins (
        admin_id INT PRIMARY KEY AUTO_INCREMENT,
        email VARCHAR(100) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        first_name VARCHAR(50) NOT NULL,
        last_name VARCHAR(50),
        role ENUM('super_admin','moderator','analyst') DEFAULT 'moderator',
        permissions JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        last_login DATETIME,
        is_active TINYINT(1) DEFAULT 1,
        INDEX idx_role (role),
        INDEX idx_active (is_active)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # ==================== ORDER TRACKING ====================
    """
    CREATE TABLE IF NOT EXISTS order_tracking (
        id INT AUTO_INCREMENT PRIMARY KEY,
        order_id INT NOT NULL,
        status VARCHAR(50) NOT NULL,
        location VARCHAR(255),
        latitude DECIMAL(10,8),
        longitude DECIMAL(11,8),
        description TEXT,
        updated_by VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (order_id) REFERENCES orders(id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # ==================== RETURN REQUESTS ====================
    """
    CREATE TABLE IF NOT EXISTS return_requests (
        id INT AUTO_INCREMENT PRIMARY KEY,
        order_id INT NOT NULL,
        buyer_id INT NOT NULL,
        reason TEXT NOT NULL,
        status ENUM('requested','approved','rejected','completed') DEFAULT 'requested',
        admin_notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (order_id) REFERENCES orders(id),
        FOREIGN KEY (buyer_id) REFERENCES buyers(id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # ==================== DISPUTES ====================
    """
    CREATE TABLE IF NOT EXISTS disputes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        order_id INT NOT NULL,
        raised_by VARCHAR(50) NOT NULL,
        raised_by_id INT NOT NULL,
        type VARCHAR(50),
        description TEXT NOT NULL,
        status ENUM('open','investigating','resolved','closed') DEFAULT 'open',
        resolution TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (order_id) REFERENCES orders(id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # ==================== AI LOGS ====================
    """
    CREATE TABLE IF NOT EXISTS ai_logs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        user_type VARCHAR(20),
        feature VARCHAR(50) NOT NULL,
        input_data JSON,
        output_data JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # ==================== REVIEW REPORTS ====================
    """
    CREATE TABLE IF NOT EXISTS review_reports (
        id INT AUTO_INCREMENT PRIMARY KEY,
        review_id INT NOT NULL,
        reported_by INT NOT NULL,
        reason TEXT NOT NULL,
        status ENUM('pending','reviewed','dismissed') DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (review_id) REFERENCES buyer_reviews(id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # ==================== OTPs (for email/login OTP verification) ====================
    """
    CREATE TABLE IF NOT EXISTS otps (
        id INT PRIMARY KEY AUTO_INCREMENT,
        email VARCHAR(255),
        phone VARCHAR(20),
        otp VARCHAR(10) NOT NULL,
        purpose VARCHAR(50) DEFAULT 'verification',
        is_verified BOOLEAN DEFAULT FALSE,
        attempts INT DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at DATETIME NOT NULL,
        INDEX idx_email (email),
        INDEX idx_phone (phone)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # ==================== PAYMENT OTPs ====================
    """
    CREATE TABLE IF NOT EXISTS payment_otps (
        id INT PRIMARY KEY AUTO_INCREMENT,
        buyer_id INT,
        buyer_phone VARCHAR(20),
        buyer_email VARCHAR(255),
        otp VARCHAR(10) NOT NULL,
        amount DECIMAL(12,2),
        product_details JSON,
        farmer_id INT,
        status ENUM('pending','verified','expired') DEFAULT 'pending',
        verified_at TIMESTAMP NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at DATETIME NOT NULL,
        INDEX idx_otp (otp),
        INDEX idx_status (status)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # ==================== RECEIPTS ====================
    """
    CREATE TABLE IF NOT EXISTS receipts (
        id INT PRIMARY KEY AUTO_INCREMENT,
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_receipt_id (receipt_id),
        INDEX idx_farmer (farmer_id),
        INDEX idx_buyer (buyer_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # ==================== RECEIPT ITEMS ====================
    """
    CREATE TABLE IF NOT EXISTS receipt_items (
        id INT PRIMARY KEY AUTO_INCREMENT,
        receipt_id INT NOT NULL,
        product_id INT,
        product_name VARCHAR(255),
        quantity_kg DECIMAL(12,2) DEFAULT 0,
        price_per_kg DECIMAL(10,2) DEFAULT 0,
        product_quality VARCHAR(50) DEFAULT 'Standard',
        item_total DECIMAL(12,2) DEFAULT 0,
        FOREIGN KEY (receipt_id) REFERENCES receipts(id) ON DELETE CASCADE,
        INDEX idx_receipt (receipt_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # ==================== TRANSACTIONS ====================
    """
    CREATE TABLE IF NOT EXISTS transactions (
        id INT PRIMARY KEY AUTO_INCREMENT,
        transaction_id VARCHAR(100) UNIQUE,
        payment_id INT,
        receipt_id INT,
        user_id INT,
        user_type VARCHAR(20),
        type ENUM('credit','debit') NOT NULL,
        amount DECIMAL(12,2) NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_transaction_id (transaction_id),
        INDEX idx_user (user_id, user_type)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
]

# Wallet ALTER statements to add missing columns
WALLET_ALTERS = [
    "ALTER TABLE wallet ADD COLUMN total_withdrawn DECIMAL(12,2) DEFAULT 0",
    "ALTER TABLE wallet ADD COLUMN withdrawal_pending DECIMAL(12,2) DEFAULT 0",
    "ALTER TABLE wallet ADD COLUMN last_withdrawal_date TIMESTAMP NULL",
]

# Update buyer_id after insert
BUYER_TRIGGER = """
DROP TRIGGER IF EXISTS update_buyer_id;
"""

BUYER_TRIGGER_2 = """
CREATE TRIGGER update_buyer_id
AFTER INSERT ON buyers
FOR EACH ROW
BEGIN
    UPDATE buyers SET buyer_id = NEW.id WHERE id = NEW.id AND buyer_id IS NULL;
END;
"""


def setup_database():
    """Create all required tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    print(f"Connected to database: {DB_NAME}")
    print(f"Host: {DB_HOST}, User: {DB_USER}")
    print("=" * 60)
    
    success_count = 0
    error_count = 0
    
    for i, sql in enumerate(TABLES):
        try:
            cursor.execute(sql)
            conn.commit()
            # Extract table name from SQL
            table_name = "unknown"
            sql_upper = sql.strip().upper()
            if "CREATE TABLE" in sql_upper:
                parts = sql.strip().split()
                for j, part in enumerate(parts):
                    if part.upper() in ('TABLE', 'EXISTS'):
                        if j + 1 < len(parts):
                            table_name = parts[j + 1].strip('(`')
                if 'IF NOT EXISTS' in sql_upper:
                    parts2 = sql.strip().split('EXISTS')
                    if len(parts2) > 1:
                        table_name = parts2[1].strip().split()[0].strip('(`')
                        
            elif "CREATE TRIGGER" in sql_upper:
                table_name = "trigger"
            
            print(f"  [OK] [{i+1}] Created/verified: {table_name}")
            success_count += 1
        except Exception as e:
            error_msg = str(e)
            # Triggers with IF NOT EXISTS may fail on older MySQL - that's OK
            if 'trigger' in sql.lower() and ('already exists' in error_msg.lower() or 'Trigger' in error_msg):
                print(f"  [WARN]  [{i+1}] Trigger already exists (OK)")
                success_count += 1
            else:
                print(f"  [ERR] [{i+1}] Error: {error_msg}")
                error_count += 1
    
    # Run wallet ALTER statements
    print("\n-- Adding missing wallet columns --")
    for alter_sql in WALLET_ALTERS:
        try:
            cursor.execute(alter_sql)
            conn.commit()
            col_name = alter_sql.split("ADD COLUMN")[1].strip().split()[0]
            print(f"  [OK] Added wallet column: {col_name}")
        except Exception as e:
            error_msg = str(e)
            if 'Duplicate column' in error_msg or 'duplicate' in error_msg.lower():
                col_name = alter_sql.split("ADD COLUMN")[1].strip().split()[0]
                print(f"  [SKIP] Wallet column already exists: {col_name}")
            else:
                print(f"  [ERR] Wallet ALTER error: {error_msg}")
    
    # Verify tables exist
    print("\n" + "=" * 60)
    print("Verifying tables...")
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    print(f"\nTables in {DB_NAME}:")
    for t in tables:
        print(f"   - {t[0]}")
    
    cursor.close()
    conn.close()
    
    print(f"\n{'=' * 60}")
    print(f"Setup complete: {success_count} succeeded, {error_count} failed")
    
    return error_count == 0


if __name__ == '__main__':
    print(">> Smart Farming Database Setup")
    print("=" * 60)
    setup_database()
