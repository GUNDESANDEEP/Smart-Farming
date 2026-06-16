-- Smart Farm Marketplace Database Schema
-- Comprehensive SQL schema for all modules

-- ============================================
-- Core Tables
-- ============================================

-- Users Table
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    role ENUM('farmer', 'buyer', 'admin') NOT NULL,
    status ENUM('active', 'inactive', 'suspended') DEFAULT 'active',
    profile_image_url VARCHAR(500),
    location VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_verified BOOLEAN DEFAULT FALSE,
    verification_token VARCHAR(255),
    verification_token_expiry DATETIME,
    INDEX idx_email (email),
    INDEX idx_phone (phone),
    INDEX idx_role (role),
    INDEX idx_status (status)
);

-- Farmers Table
CREATE TABLE farmers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL UNIQUE,
    farm_name VARCHAR(255) NOT NULL,
    farm_location VARCHAR(255) NOT NULL,
    farm_size DECIMAL(10, 2),
    farm_size_unit ENUM('acres', 'hectares') DEFAULT 'acres',
    phone_verified BOOLEAN DEFAULT FALSE,
    email_verified BOOLEAN DEFAULT FALSE,
    average_rating DECIMAL(3, 2) DEFAULT 0,
    total_reviews INT DEFAULT 0,
    total_sales INT DEFAULT 0,
    total_earnings DECIMAL(12, 2) DEFAULT 0,
    bank_account_number VARCHAR(20),
    bank_name VARCHAR(255),
    ifsc_code VARCHAR(11),
    aadhar_number VARCHAR(12),
    pan_number VARCHAR(10),
    documents_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_average_rating (average_rating),
    INDEX idx_verified (documents_verified)
);

-- Buyers Table
CREATE TABLE buyers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL UNIQUE,
    phone_verified BOOLEAN DEFAULT FALSE,
    email_verified BOOLEAN DEFAULT FALSE,
    preferred_delivery_address_id INT,
    loyalty_points INT DEFAULT 0,
    total_spent DECIMAL(12, 2) DEFAULT 0,
    total_orders INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_verified (phone_verified)
);

-- ============================================
-- Product Tables
-- ============================================

-- Products Table
CREATE TABLE products (
    id INT PRIMARY KEY AUTO_INCREMENT,
    farmer_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL,
    sub_category VARCHAR(100),
    price DECIMAL(10, 2) NOT NULL,
    price_unit ENUM('kg', 'piece', 'liter', 'quintal') NOT NULL,
    stock_quantity DECIMAL(12, 2) NOT NULL,
    unit_of_measure ENUM('kg', 'piece', 'liter', 'quintal') NOT NULL,
    image_url VARCHAR(500),
    harvest_date DATE,
    expiry_date DATE,
    status ENUM('pending', 'approved', 'rejected', 'discontinued') DEFAULT 'pending',
    rejection_reason TEXT,
    organic BOOLEAN DEFAULT FALSE,
    pesticide_free BOOLEAN DEFAULT FALSE,
    certification_url VARCHAR(500),
    average_rating DECIMAL(3, 2) DEFAULT 0,
    total_reviews INT DEFAULT 0,
    total_sold INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE CASCADE,
    INDEX idx_category (category),
    INDEX idx_status (status),
    INDEX idx_farmer_id (farmer_id),
    INDEX idx_price (price),
    INDEX idx_organic (organic),
    FULLTEXT INDEX ft_search (name, description)
);

-- Product Images Table
CREATE TABLE product_images (
    id INT PRIMARY KEY AUTO_INCREMENT,
    product_id INT NOT NULL,
    image_url VARCHAR(500) NOT NULL,
    alt_text VARCHAR(255),
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    INDEX idx_product_id (product_id)
);

-- ============================================
-- Order Tables
-- ============================================

-- Orders Table
CREATE TABLE orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    buyer_id INT NOT NULL,
    farmer_id INT NOT NULL,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    total_amount DECIMAL(12, 2) NOT NULL,
    tax_amount DECIMAL(10, 2) DEFAULT 0,
    delivery_charge DECIMAL(10, 2) DEFAULT 0,
    discount_amount DECIMAL(10, 2) DEFAULT 0,
    status ENUM('pending', 'confirmed', 'packed', 'shipped', 'delivered', 'cancelled', 'returned') DEFAULT 'pending',
    delivery_address TEXT NOT NULL,
    delivery_date DATE,
    estimated_delivery_date DATE,
    payment_method ENUM('razorpay', 'cod', 'wallet', 'bank_transfer') NOT NULL,
    payment_status ENUM('pending', 'completed', 'failed', 'refunded') DEFAULT 'pending',
    payment_id VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (buyer_id) REFERENCES buyers(id) ON DELETE CASCADE,
    FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE CASCADE,
    INDEX idx_buyer_id (buyer_id),
    INDEX idx_farmer_id (farmer_id),
    INDEX idx_status (status),
    INDEX idx_payment_status (payment_status),
    INDEX idx_created_at (created_at)
);

-- Order Items Table
CREATE TABLE order_items (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity DECIMAL(12, 2) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(12, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id),
    INDEX idx_order_id (order_id)
);

-- ============================================
-- Payment Tables
-- ============================================

-- Payments Table
CREATE TABLE payments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    payment_method ENUM('razorpay', 'cod', 'wallet', 'bank_transfer') NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'INR',
    payment_id VARCHAR(100),
    payment_gateway_response JSON,
    status ENUM('pending', 'completed', 'failed', 'refunded') DEFAULT 'pending',
    transaction_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    INDEX idx_order_id (order_id),
    INDEX idx_status (status),
    INDEX idx_payment_id (payment_id)
);

-- Wallets Table
CREATE TABLE wallets (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL UNIQUE,
    balance DECIMAL(12, 2) DEFAULT 0,
    total_credits DECIMAL(12, 2) DEFAULT 0,
    total_debits DECIMAL(12, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id)
);

-- Wallet Transactions Table
CREATE TABLE wallet_transactions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    wallet_id INT NOT NULL,
    type ENUM('credit', 'debit') NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    description VARCHAR(255),
    reference_id INT,
    reference_type ENUM('order', 'refund', 'earnings', 'cashback') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (wallet_id) REFERENCES wallets(id) ON DELETE CASCADE,
    INDEX idx_wallet_id (wallet_id),
    INDEX idx_reference (reference_type, reference_id)
);

-- ============================================
-- Review & Rating Tables
-- ============================================

-- Reviews Table
CREATE TABLE reviews (
    id INT PRIMARY KEY AUTO_INCREMENT,
    product_id INT NOT NULL,
    order_id INT NOT NULL,
    buyer_id INT NOT NULL,
    farmer_id INT NOT NULL,
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    review_text TEXT,
    images JSON,
    helpful_count INT DEFAULT 0,
    unhelpful_count INT DEFAULT 0,
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (buyer_id) REFERENCES buyers(id),
    FOREIGN KEY (farmer_id) REFERENCES farmers(id),
    INDEX idx_product_id (product_id),
    INDEX idx_farmer_id (farmer_id),
    INDEX idx_rating (rating)
);

-- ============================================
-- Cart Tables
-- ============================================

-- Shopping Carts Table
CREATE TABLE shopping_carts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    buyer_id INT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (buyer_id) REFERENCES buyers(id) ON DELETE CASCADE
);

-- Cart Items Table
CREATE TABLE cart_items (
    id INT PRIMARY KEY AUTO_INCREMENT,
    cart_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity DECIMAL(12, 2) NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cart_id) REFERENCES shopping_carts(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id),
    UNIQUE KEY unique_cart_product (cart_id, product_id),
    INDEX idx_cart_id (cart_id)
);

-- Wishlist Table
CREATE TABLE wishlist (
    id INT PRIMARY KEY AUTO_INCREMENT,
    buyer_id INT NOT NULL,
    product_id INT NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (buyer_id) REFERENCES buyers(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id),
    UNIQUE KEY unique_buyer_product (buyer_id, product_id),
    INDEX idx_buyer_id (buyer_id)
);

-- ============================================
-- Delivery & Tracking Tables
-- ============================================

-- Delivery Addresses Table
CREATE TABLE delivery_addresses (
    id INT PRIMARY KEY AUTO_INCREMENT,
    buyer_id INT NOT NULL,
    address_line1 VARCHAR(255) NOT NULL,
    address_line2 VARCHAR(255),
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    postal_code VARCHAR(10) NOT NULL,
    country VARCHAR(100) DEFAULT 'India',
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (buyer_id) REFERENCES buyers(id) ON DELETE CASCADE,
    INDEX idx_buyer_id (buyer_id)
);

-- Order Tracking Table
CREATE TABLE order_tracking (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    status ENUM('pending', 'confirmed', 'packed', 'shipped', 'in_transit', 'delivered', 'cancelled', 'returned') NOT NULL,
    location VARCHAR(255),
    latitude DECIMAL(9, 6),
    longitude DECIMAL(9, 6),
    notes TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    INDEX idx_order_id (order_id),
    INDEX idx_status (status)
);

-- ============================================
-- Chat & Communication Tables
-- ============================================

-- Conversations Table
CREATE TABLE conversations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    farmer_id INT NOT NULL,
    buyer_id INT NOT NULL,
    order_id INT,
    last_message_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (farmer_id) REFERENCES farmers(id),
    FOREIGN KEY (buyer_id) REFERENCES buyers(id),
    FOREIGN KEY (order_id) REFERENCES orders(id),
    UNIQUE KEY unique_farmer_buyer (farmer_id, buyer_id),
    INDEX idx_farmer_id (farmer_id),
    INDEX idx_buyer_id (buyer_id)
);

-- Messages Table
CREATE TABLE messages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    conversation_id INT NOT NULL,
    sender_id INT NOT NULL,
    message_text TEXT NOT NULL,
    image_url VARCHAR(500),
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (sender_id) REFERENCES users(id),
    INDEX idx_conversation_id (conversation_id),
    INDEX idx_is_read (is_read)
);

-- ============================================
-- Notification Tables
-- ============================================

-- Notifications Table
CREATE TABLE notifications (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    type ENUM('order', 'payment', 'product', 'system', 'promotion') NOT NULL,
    reference_id INT,
    reference_type VARCHAR(50),
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_is_read (is_read),
    INDEX idx_created_at (created_at)
);

-- ============================================
-- Analytics & Reporting Tables
-- ============================================

-- AI Logs Table
CREATE TABLE ai_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    model_name VARCHAR(100) NOT NULL,
    input_data JSON,
    output_data JSON,
    processing_time_ms INT,
    accuracy DECIMAL(5, 2),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_model_name (model_name),
    INDEX idx_created_at (created_at)
);

-- Weather Data Table
CREATE TABLE weather_data (
    id INT PRIMARY KEY AUTO_INCREMENT,
    location VARCHAR(255) NOT NULL,
    temperature_min DECIMAL(5, 2),
    temperature_max DECIMAL(5, 2),
    humidity DECIMAL(5, 2),
    rainfall DECIMAL(10, 2),
    wind_speed DECIMAL(8, 2),
    forecast_date DATE NOT NULL,
    data_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (farmer_id) REFERENCES farmers(id),
    INDEX idx_location (location),
    INDEX idx_forecast_date (forecast_date)
);

-- Crop Recommendations Table
CREATE TABLE crop_recommendations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    farmer_id INT NOT NULL,
    location VARCHAR(255) NOT NULL,
    season VARCHAR(50),
    recommended_crops JSON,
    confidence_score DECIMAL(5, 2),
    reasoning TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (farmer_id) REFERENCES farmers(id),
    INDEX idx_farmer_id (farmer_id)
);

-- Price Forecasting Table
CREATE TABLE price_forecast (
    id INT PRIMARY KEY AUTO_INCREMENT,
    crop_name VARCHAR(100) NOT NULL,
    location VARCHAR(255),
    forecasted_price DECIMAL(10, 2),
    confidence_score DECIMAL(5, 2),
    forecast_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_crop_name (crop_name),
    INDEX idx_forecast_date (forecast_date)
);

-- ============================================
-- Admin Tables
-- ============================================

-- Disputes Table
CREATE TABLE disputes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    initiator_id INT NOT NULL,
    dispute_type ENUM('quality', 'quantity', 'delivery', 'payment', 'other') NOT NULL,
    description TEXT NOT NULL,
    status ENUM('open', 'investigating', 'resolved', 'closed') DEFAULT 'open',
    resolution TEXT,
    resolved_by INT,
    resolved_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (initiator_id) REFERENCES users(id),
    FOREIGN KEY (resolved_by) REFERENCES users(id),
    INDEX idx_status (status),
    INDEX idx_order_id (order_id)
);

-- Audit Logs Table
CREATE TABLE audit_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    admin_id INT NOT NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id INT,
    old_values JSON,
    new_values JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES users(id),
    INDEX idx_action (action),
    INDEX idx_created_at (created_at)
);

-- ============================================
-- Indexes for Performance
-- ============================================

CREATE INDEX idx_orders_buyer_created ON orders(buyer_id, created_at);
CREATE INDEX idx_orders_farmer_created ON orders(farmer_id, created_at);
CREATE INDEX idx_products_category_price ON products(category, price);
CREATE INDEX idx_products_farmer_status ON products(farmer_id, status);

-- ============================================
-- Views for Common Queries
-- ============================================

CREATE VIEW farmer_earnings_summary AS
SELECT 
    f.id,
    f.user_id,
    f.farm_name,
    COUNT(DISTINCT o.id) as total_orders,
    SUM(o.total_amount) as total_earnings,
    AVG(r.rating) as average_rating,
    COUNT(DISTINCT r.id) as total_reviews
FROM farmers f
LEFT JOIN orders o ON f.id = o.farmer_id AND o.status = 'delivered'
LEFT JOIN reviews r ON f.id = r.farmer_id
GROUP BY f.id, f.user_id, f.farm_name;

CREATE VIEW product_performance AS
SELECT 
    p.id,
    p.name,
    p.farmer_id,
    COUNT(oi.id) as times_sold,
    SUM(oi.quantity) as total_quantity_sold,
    AVG(r.rating) as average_rating,
    COUNT(DISTINCT r.id) as total_reviews
FROM products p
LEFT JOIN order_items oi ON p.id = oi.product_id
LEFT JOIN reviews r ON p.id = r.product_id
GROUP BY p.id, p.name, p.farmer_id;

-- ============================================
-- End of Schema
-- ============================================
