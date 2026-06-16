-- ============================================================================
-- SMART FARMER MARKETPLACE - COMPLETE PRODUCTION DATABASE SCHEMA
-- Database: smart_farming_db
-- ============================================================================

-- DROP existing database and create new
DROP DATABASE IF EXISTS smart_farming_db;
CREATE DATABASE smart_farming_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE smart_farming_db;

-- ============================================================================
-- 1. ROLES TABLE
-- ============================================================================
CREATE TABLE roles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) UNIQUE NOT NULL, -- farmer, buyer, admin
    description TEXT,
    permissions JSON, -- JSON array of permission strings
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default roles
INSERT INTO roles (name, description, permissions) VALUES
('farmer', 'Farmer user role', '["create_profile", "manage_products", "manage_orders", "view_earnings", "chat"]'),
('buyer', 'Buyer user role', '["search_products", "place_orders", "make_payments", "track_orders", "chat", "leave_reviews"]'),
('admin', 'Administrator role', '["manage_users", "manage_products", "manage_transactions", "view_analytics", "suspend_accounts"]');

-- ============================================================================
-- 2. USERS TABLE (Base user table for all roles)
-- ============================================================================
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(15) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50),
    profile_image VARCHAR(500),
    role_id INT NOT NULL,
    status VARCHAR(50) DEFAULT 'active', -- active, suspended, deleted, inactive
    is_verified BOOLEAN DEFAULT FALSE,
    email_verified_at TIMESTAMP NULL,
    phone_verified_at TIMESTAMP NULL,
    last_login TIMESTAMP NULL,
    firebase_uid VARCHAR(255) UNIQUE,
    two_factor_enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id),
    INDEX idx_email (email),
    INDEX idx_phone (phone),
    INDEX idx_role_id (role_id),
    INDEX idx_status (status),
    INDEX idx_firebase_uid (firebase_uid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 3. FARMERS TABLE
-- ============================================================================
CREATE TABLE farmers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT UNIQUE NOT NULL,
    aadhar_number VARCHAR(12) UNIQUE,
    pan_number VARCHAR(10) UNIQUE,
    bank_account VARCHAR(20),
    bank_ifsc VARCHAR(11),
    bank_name VARCHAR(100),
    location VARCHAR(255) NOT NULL,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    land_area_hectares DECIMAL(8, 2),
    crops_grown JSON, -- ["rice", "wheat", "corn"]
    experience_years INT DEFAULT 0,
    certificate_image VARCHAR(500),
    is_verified BOOLEAN DEFAULT FALSE,
    verification_date TIMESTAMP NULL,
    verification_document VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_location (location),
    INDEX idx_is_verified (is_verified)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 4. BUYERS TABLE
-- ============================================================================
CREATE TABLE buyers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT UNIQUE NOT NULL,
    business_name VARCHAR(150),
    business_type VARCHAR(50), -- retail, wholesale, restaurant, exporter
    company_registration VARCHAR(50),
    location VARCHAR(255) NOT NULL,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    delivery_address TEXT,
    gst_number VARCHAR(15),
    is_verified BOOLEAN DEFAULT FALSE,
    verification_date TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_location (location)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 5. ADMINS TABLE
-- ============================================================================
CREATE TABLE admins (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT UNIQUE NOT NULL,
    admin_level VARCHAR(50) DEFAULT 'moderator', -- super_admin, admin, moderator
    department VARCHAR(100),
    permissions JSON,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES admins(user_id),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 6. CATEGORIES TABLE
-- ============================================================================
CREATE TABLE categories (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    icon VARCHAR(100),
    image VARCHAR(500),
    parent_category_id INT,
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_category_id) REFERENCES categories(id) ON DELETE SET NULL,
    INDEX idx_slug (slug),
    INDEX idx_parent_category_id (parent_category_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default categories
INSERT INTO categories (name, slug, description, is_active) VALUES
('Vegetables', 'vegetables', 'Fresh vegetables', TRUE),
('Fruits', 'fruits', 'Fresh fruits', TRUE),
('Grains', 'grains', 'Grains and cereals', TRUE),
('Pulses', 'pulses', 'Pulses and legumes', TRUE),
('Dairy', 'dairy', 'Dairy products', TRUE),
('Spices', 'spices', 'Spices and condiments', TRUE),
('Herbs', 'herbs', 'Fresh herbs', TRUE),
('Flowers', 'flowers', 'Fresh flowers', TRUE);

-- ============================================================================
-- 7. PRODUCTS TABLE
-- ============================================================================
CREATE TABLE products (
    id INT PRIMARY KEY AUTO_INCREMENT,
    farmer_id INT NOT NULL,
    category_id INT NOT NULL,
    name VARCHAR(150) NOT NULL,
    slug VARCHAR(150) UNIQUE NOT NULL,
    description TEXT,
    detailed_description LONGTEXT,
    quantity INT NOT NULL,
    unit VARCHAR(20) DEFAULT 'kg', -- kg, ton, bags, pieces, liters
    price DECIMAL(10, 2) NOT NULL,
    min_order_quantity INT DEFAULT 1,
    max_order_quantity INT,
    discount_percentage DECIMAL(5, 2) DEFAULT 0,
    location VARCHAR(255),
    harvest_date DATE,
    expiry_date DATE,
    images JSON, -- [{"url": "...", "alt": "..."}, ...]
    specifications JSON,
    certifications JSON,
    is_organic BOOLEAN DEFAULT FALSE,
    is_available BOOLEAN DEFAULT TRUE,
    total_sold INT DEFAULT 0,
    average_rating DECIMAL(3, 2) DEFAULT 0.0,
    review_count INT DEFAULT 0,
    views_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id),
    INDEX idx_farmer_id (farmer_id),
    INDEX idx_category_id (category_id),
    INDEX idx_slug (slug),
    INDEX idx_is_available (is_available),
    INDEX idx_created_at (created_at),
    FULLTEXT INDEX ft_search (name, description)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 8. CARTS TABLE
-- ============================================================================
CREATE TABLE carts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    buyer_id INT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (buyer_id) REFERENCES buyers(id) ON DELETE CASCADE,
    INDEX idx_buyer_id (buyer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 9. CART ITEMS TABLE
-- ============================================================================
CREATE TABLE cart_items (
    id INT PRIMARY KEY AUTO_INCREMENT,
    cart_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cart_id) REFERENCES carts(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    INDEX idx_cart_id (cart_id),
    INDEX idx_product_id (product_id),
    UNIQUE KEY unique_cart_product (cart_id, product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 10. ORDERS TABLE
-- ============================================================================
CREATE TABLE orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    farmer_id INT NOT NULL,
    buyer_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    total_price DECIMAL(12, 2) NOT NULL,
    discount_amount DECIMAL(10, 2) DEFAULT 0,
    tax_amount DECIMAL(10, 2) DEFAULT 0,
    shipping_cost DECIMAL(10, 2) DEFAULT 0,
    final_price DECIMAL(12, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending', -- pending, confirmed, paid, processing, shipped, delivered, cancelled, returned
    payment_status VARCHAR(50) DEFAULT 'pending', -- pending, paid, failed, refunded
    delivery_status VARCHAR(50) DEFAULT 'pending', -- pending, picked_up, in_transit, out_for_delivery, delivered
    delivery_address TEXT NOT NULL,
    delivery_date DATE,
    delivered_date TIMESTAMP NULL,
    delivery_latitude DECIMAL(10, 8),
    delivery_longitude DECIMAL(11, 8),
    notes TEXT,
    rejection_reason VARCHAR(255),
    cancellation_reason VARCHAR(255),
    tracking_number VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (farmer_id) REFERENCES farmers(id),
    FOREIGN KEY (buyer_id) REFERENCES buyers(id),
    FOREIGN KEY (product_id) REFERENCES products(id),
    INDEX idx_farmer_id (farmer_id),
    INDEX idx_buyer_id (buyer_id),
    INDEX idx_status (status),
    INDEX idx_payment_status (payment_status),
    INDEX idx_created_at (created_at),
    INDEX idx_order_number (order_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 11. PAYMENTS TABLE
-- ============================================================================
CREATE TABLE payments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    buyer_id INT NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'INR',
    payment_method VARCHAR(50), -- razorpay, upi, netbanking, wallet, cod
    transaction_id VARCHAR(100),
    razorpay_payment_id VARCHAR(100),
    razorpay_order_id VARCHAR(100),
    razorpay_signature VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending', -- pending, completed, failed, refunded
    refund_amount DECIMAL(12, 2) DEFAULT 0,
    refund_transaction_id VARCHAR(100),
    error_message TEXT,
    payment_date TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (buyer_id) REFERENCES buyers(id),
    INDEX idx_order_id (order_id),
    INDEX idx_buyer_id (buyer_id),
    INDEX idx_status (status),
    INDEX idx_transaction_id (transaction_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 12. REVIEWS & RATINGS TABLE
-- ============================================================================
CREATE TABLE reviews (
    id INT PRIMARY KEY AUTO_INCREMENT,
    product_id INT NOT NULL,
    order_id INT,
    buyer_id INT NOT NULL,
    farmer_id INT,
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    title VARCHAR(255),
    comment TEXT,
    review_images JSON,
    is_verified_purchase BOOLEAN DEFAULT TRUE,
    helpful_count INT DEFAULT 0,
    unhelpful_count INT DEFAULT 0,
    is_approved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE SET NULL,
    FOREIGN KEY (buyer_id) REFERENCES buyers(id),
    FOREIGN KEY (farmer_id) REFERENCES farmers(id),
    INDEX idx_product_id (product_id),
    INDEX idx_buyer_id (buyer_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 13. MESSAGES/CHAT TABLE
-- ============================================================================
CREATE TABLE messages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    conversation_id INT NOT NULL,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    content TEXT NOT NULL,
    attachment_url VARCHAR(500),
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sender_id) REFERENCES users(id),
    FOREIGN KEY (receiver_id) REFERENCES users(id),
    INDEX idx_conversation_id (conversation_id),
    INDEX idx_sender_id (sender_id),
    INDEX idx_is_read (is_read),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 14. CONVERSATIONS TABLE
-- ============================================================================
CREATE TABLE conversations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_1_id INT NOT NULL,
    user_2_id INT NOT NULL,
    last_message_id INT,
    last_message_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_1_id) REFERENCES users(id),
    FOREIGN KEY (user_2_id) REFERENCES users(id),
    UNIQUE KEY unique_conversation (user_1_id, user_2_id),
    INDEX idx_user_1_id (user_1_id),
    INDEX idx_user_2_id (user_2_id),
    INDEX idx_last_message_at (last_message_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 15. WALLET TABLE
-- ============================================================================
CREATE TABLE wallets (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT UNIQUE NOT NULL,
    balance DECIMAL(12, 2) DEFAULT 0.0,
    total_earned DECIMAL(12, 2) DEFAULT 0.0,
    total_withdrawn DECIMAL(12, 2) DEFAULT 0.0,
    pending_amount DECIMAL(12, 2) DEFAULT 0.0,
    last_withdrawal_date TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 16. TRANSACTIONS TABLE
-- ============================================================================
CREATE TABLE transactions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    type VARCHAR(50) NOT NULL, -- credit, debit, withdrawal, refund, commission
    amount DECIMAL(12, 2) NOT NULL,
    description TEXT,
    order_id INT,
    payment_id INT,
    method VARCHAR(50), -- wallet, bank_transfer, razorpay, upi
    gateway_transaction_id VARCHAR(100),
    status VARCHAR(50) DEFAULT 'completed', -- pending, completed, failed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE SET NULL,
    FOREIGN KEY (payment_id) REFERENCES payments(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_type (type),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 17. NOTIFICATIONS TABLE
-- ============================================================================
CREATE TABLE notifications (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT,
    type VARCHAR(50), -- order, payment, review, message, system, promotion
    data JSON,
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP NULL,
    action_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_is_read (is_read),
    INDEX idx_type (type),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 18. WEATHER TABLE
-- ============================================================================
CREATE TABLE weather (
    id INT PRIMARY KEY AUTO_INCREMENT,
    location VARCHAR(255) NOT NULL,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    temperature DECIMAL(5, 2),
    feels_like DECIMAL(5, 2),
    humidity INT,
    rainfall DECIMAL(8, 2),
    wind_speed DECIMAL(6, 2),
    pressure INT,
    weather_condition VARCHAR(100),
    weather_description TEXT,
    forecast_7days JSON,
    forecast_14days JSON,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_location (location),
    INDEX idx_coordinates (latitude, longitude),
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 19. OTP VERIFICATION TABLE
-- ============================================================================
CREATE TABLE otp_verification (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(100),
    phone VARCHAR(15),
    otp VARCHAR(6) NOT NULL,
    purpose VARCHAR(50), -- registration, login, password_reset, email_verification
    attempts INT DEFAULT 0,
    is_verified BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMP NOT NULL,
    verified_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email_otp (email, otp),
    INDEX idx_phone_otp (phone, otp),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 20. PASSWORD RESETS TABLE
-- ============================================================================
CREATE TABLE password_resets (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    email VARCHAR(100) NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_token (token),
    INDEX idx_email (email),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 21. WISHLIST TABLE
-- ============================================================================
CREATE TABLE wishlists (
    id INT PRIMARY KEY AUTO_INCREMENT,
    buyer_id INT NOT NULL,
    product_id INT NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (buyer_id) REFERENCES buyers(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    UNIQUE KEY unique_wishlist (buyer_id, product_id),
    INDEX idx_buyer_id (buyer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 22. RATINGS TABLE (Farmer ratings)
-- ============================================================================
CREATE TABLE farmer_ratings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    farmer_id INT NOT NULL,
    order_id INT,
    buyer_id INT NOT NULL,
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    quality_rating INT,
    timeliness_rating INT,
    communication_rating INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (farmer_id) REFERENCES farmers(id),
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (buyer_id) REFERENCES buyers(id),
    INDEX idx_farmer_id (farmer_id),
    INDEX idx_buyer_id (buyer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 23. ANALYTICS TABLE
-- ============================================================================
CREATE TABLE analytics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    entity_type VARCHAR(50), -- user, farmer, product, order
    entity_id INT,
    metric_type VARCHAR(50), -- views, clicks, conversions, revenue
    value INT DEFAULT 0,
    date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_entity (entity_type, entity_id),
    INDEX idx_date (date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 24. AI PREDICTIONS TABLE
-- ============================================================================
CREATE TABLE ai_predictions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    farmer_id INT NOT NULL,
    prediction_type VARCHAR(50), -- crop_recommendation, price_prediction, disease_detection, yield_forecast
    location VARCHAR(255),
    crop_name VARCHAR(100),
    season VARCHAR(20),
    prediction_data JSON,
    confidence_score DECIMAL(5, 2),
    model_version VARCHAR(50),
    is_applied BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (farmer_id) REFERENCES farmers(id),
    INDEX idx_farmer_id (farmer_id),
    INDEX idx_type (prediction_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 25. AUDIT LOG TABLE
-- ============================================================================
CREATE TABLE audit_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id INT,
    changes JSON,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_user_id (user_id),
    INDEX idx_action (action),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- INDEXES FOR PERFORMANCE OPTIMIZATION
-- ============================================================================
ALTER TABLE users ADD INDEX idx_created_at (created_at);
ALTER TABLE products ADD INDEX idx_price (price);
ALTER TABLE orders ADD INDEX idx_updated_at (updated_at);
ALTER TABLE messages ADD INDEX idx_updated_at (updated_at);

-- ============================================================================
-- STORED PROCEDURES FOR COMMON OPERATIONS
-- ============================================================================

-- Get total sales for a farmer
DELIMITER $$
CREATE PROCEDURE sp_get_farmer_sales(IN farmer_id_param INT)
BEGIN
    SELECT 
        COUNT(DISTINCT id) as total_orders,
        SUM(final_price) as total_sales,
        COUNT(DISTINCT CASE WHEN status = 'delivered' THEN id END) as delivered_orders,
        AVG(CASE WHEN farmer_ratings.rating IS NOT NULL THEN farmer_ratings.rating ELSE 0 END) as average_rating
    FROM orders
    LEFT JOIN farmer_ratings ON orders.id = farmer_ratings.order_id
    WHERE farmer_id = farmer_id_param;
END$$
DELIMITER ;

-- Get product statistics
DELIMITER $$
CREATE PROCEDURE sp_get_product_stats(IN product_id_param INT)
BEGIN
    SELECT 
        p.id,
        p.name,
        p.total_sold,
        p.average_rating,
        p.review_count,
        p.views_count,
        COUNT(DISTINCT r.id) as total_reviews,
        AVG(r.rating) as avg_rating
    FROM products p
    LEFT JOIN reviews r ON p.id = r.product_id
    WHERE p.id = product_id_param
    GROUP BY p.id;
END$$
DELIMITER ;

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
