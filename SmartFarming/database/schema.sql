-- Smart Farming Database Schema - Farmer Module
-- Database: smart_farming_db

-- 1. FARMERS TABLE (Core user data)
CREATE TABLE farmers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    phone VARCHAR(15) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50),
    aadhar_number VARCHAR(12) UNIQUE,
    bank_account VARCHAR(20),
    bank_ifsc VARCHAR(11),
    bank_name VARCHAR(100),
    profile_image VARCHAR(255),
    location VARCHAR(255) NOT NULL,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    land_area_hectares DECIMAL(8, 2),
    crops_grown VARCHAR(255),
    experience_years INT,
    is_verified BOOLEAN DEFAULT FALSE,
    verification_date TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_phone (phone),
    INDEX idx_email (email),
    INDEX idx_location (location)
);

-- 2. OTP VERIFICATION TABLE
CREATE TABLE otp_verification (
    id INT PRIMARY KEY AUTO_INCREMENT,
    phone VARCHAR(15) NOT NULL,
    otp VARCHAR(6) NOT NULL,
    attempts INT DEFAULT 0,
    is_verified BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_phone_otp (phone, otp)
);

-- 3. PRODUCTS TABLE (Farmer's products)
CREATE TABLE products (
    id INT PRIMARY KEY AUTO_INCREMENT,
    farmer_id INT NOT NULL,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL, -- rice, wheat, cotton, vegetables, fruits
    subcategory VARCHAR(50),
    quantity INT NOT NULL,
    unit VARCHAR(20) DEFAULT 'kg', -- kg, ton, bags, pieces
    price DECIMAL(10, 2) NOT NULL,
    min_order_quantity INT DEFAULT 1,
    location VARCHAR(255),
    harvest_date DATE,
    expiry_date DATE,
    images JSON, -- [url1, url2, url3]
    is_available BOOLEAN DEFAULT TRUE,
    total_sold INT DEFAULT 0,
    rating DECIMAL(3, 2) DEFAULT 0.0,
    review_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE CASCADE,
    INDEX idx_farmer_id (farmer_id),
    INDEX idx_category (category),
    INDEX idx_available (is_available)
);

-- 4. ORDERS TABLE (Orders from buyers)
CREATE TABLE orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    farmer_id INT NOT NULL,
    buyer_id INT, -- Buyer ID (will be added in buyer module)
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    total_price DECIMAL(12, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending', -- pending, accepted, rejected, in_transit, delivered, cancelled
    payment_status VARCHAR(50) DEFAULT 'pending', -- pending, completed, failed
    delivery_address TEXT,
    delivery_date DATE,
    delivery_latitude DECIMAL(10, 8),
    delivery_longitude DECIMAL(11, 8),
    notes TEXT,
    rejection_reason VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT,
    INDEX idx_farmer_id (farmer_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);

-- 5. AI PREDICTIONS TABLE (Crop recommendations, price predictions)
CREATE TABLE ai_predictions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    farmer_id INT NOT NULL,
    prediction_type VARCHAR(50) NOT NULL, -- crop_recommendation, price_prediction, fertilizer_suggestion, disease_detection
    location VARCHAR(255),
    crop_name VARCHAR(100),
    season VARCHAR(20),
    prediction_data JSON, -- stores recommendation/prediction details
    confidence_score DECIMAL(5, 2),
    model_version VARCHAR(50),
    is_applied BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE CASCADE,
    INDEX idx_farmer_id (farmer_id),
    INDEX idx_type (prediction_type),
    INDEX idx_created_at (created_at)
);

-- 6. WALLET TABLE (Farmer's earnings)
CREATE TABLE wallet (
    id INT PRIMARY KEY AUTO_INCREMENT,
    farmer_id INT NOT NULL UNIQUE,
    balance DECIMAL(12, 2) DEFAULT 0.0,
    total_earnings DECIMAL(12, 2) DEFAULT 0.0,
    total_withdrawn DECIMAL(12, 2) DEFAULT 0.0,
    withdrawal_pending DECIMAL(12, 2) DEFAULT 0.0,
    last_withdrawal_date TIMESTAMP NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE CASCADE,
    INDEX idx_farmer_id (farmer_id)
);

-- 7. TRANSACTIONS TABLE (Payment history)
CREATE TABLE transactions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    farmer_id INT NOT NULL,
    transaction_type VARCHAR(50) NOT NULL, -- credit, debit, withdrawal, refund
    amount DECIMAL(12, 2) NOT NULL,
    description TEXT,
    order_id INT,
    payment_method VARCHAR(50), -- wallet, bank_transfer, razorpay, upi
    payment_gateway_id VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending', -- pending, completed, failed, cancelled
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE CASCADE,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE SET NULL,
    INDEX idx_farmer_id (farmer_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);

-- 8. WEATHER TABLE (Real-time weather data)
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
    forecast_7days JSON, -- array of 7-day forecast
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_location (location),
    INDEX idx_updated_at (updated_at)
);

-- 9. NOTIFICATIONS TABLE
CREATE TABLE notifications (
    id INT PRIMARY KEY AUTO_INCREMENT,
    farmer_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT,
    type VARCHAR(50), -- order, payment, ai_suggestion, weather_alert, general
    is_read BOOLEAN DEFAULT FALSE,
    action_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE CASCADE,
    INDEX idx_farmer_id (farmer_id),
    INDEX idx_is_read (is_read),
    INDEX idx_created_at (created_at)
);

-- 10. REVIEWS & RATINGS TABLE
CREATE TABLE reviews (
    id INT PRIMARY KEY AUTO_INCREMENT,
    product_id INT NOT NULL,
    buyer_id INT,
    rating INT CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    INDEX idx_product_id (product_id),
    INDEX idx_created_at (created_at)
);

-- INDEXES FOR PERFORMANCE
CREATE INDEX idx_wallet_farmer ON wallet(farmer_id);
CREATE INDEX idx_transaction_farmer_date ON transactions(farmer_id, created_at);
CREATE INDEX idx_orders_farmer_status_date ON orders(farmer_id, status, created_at);
CREATE INDEX idx_products_farmer_category ON products(farmer_id, category);
CREATE INDEX idx_predictions_farmer_date ON ai_predictions(farmer_id, created_at);
