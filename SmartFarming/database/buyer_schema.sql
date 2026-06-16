-- ====================================================================
-- BUYER MODULE DATABASE SCHEMA
-- Add to existing smart_farming_db
-- ====================================================================

-- ====================================================================
-- 1. BUYERS TABLE (New) - Buyer user profiles
-- ====================================================================
CREATE TABLE IF NOT EXISTS buyers (
  buyer_id INT PRIMARY KEY AUTO_INCREMENT,
  phone VARCHAR(10) UNIQUE NOT NULL,
  email VARCHAR(100) UNIQUE NOT NULL,
  first_name VARCHAR(50) NOT NULL,
  last_name VARCHAR(50),
  password_hash VARCHAR(255) NOT NULL,
  location VARCHAR(100),
  latitude DECIMAL(10, 8),
  longitude DECIMAL(11, 8),
  address TEXT,
  city VARCHAR(50),
  state VARCHAR(50),
  pincode VARCHAR(6),
  is_verified BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_phone (phone),
  INDEX idx_email (email),
  INDEX idx_location (location)
);

-- ====================================================================
-- 2. CART TABLE (New) - Shopping cart items per buyer
-- ====================================================================
CREATE TABLE IF NOT EXISTS cart (
  cart_id INT PRIMARY KEY AUTO_INCREMENT,
  buyer_id INT NOT NULL,
  product_id INT NOT NULL,
  farmer_id INT NOT NULL,
  quantity INT NOT NULL DEFAULT 1,
  price_at_addition DECIMAL(10, 2),
  added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (buyer_id) REFERENCES buyers(buyer_id) ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
  FOREIGN KEY (farmer_id) REFERENCES farmers(farmer_id) ON DELETE RESTRICT,
  UNIQUE KEY unique_cart_item (buyer_id, product_id),
  INDEX idx_buyer (buyer_id),
  INDEX idx_product (product_id)
);

-- ====================================================================
-- 3. PAYMENTS TABLE (New) - Payment records for orders
-- ====================================================================
CREATE TABLE IF NOT EXISTS payments (
  payment_id INT PRIMARY KEY AUTO_INCREMENT,
  order_id INT NOT NULL,
  buyer_id INT NOT NULL,
  amount DECIMAL(10, 2) NOT NULL,
  payment_method ENUM('upi', 'card', 'cod', 'netbanking') NOT NULL,
  status ENUM('pending', 'completed', 'failed', 'refunded') DEFAULT 'pending',
  transaction_id VARCHAR(100) UNIQUE,
  payment_gateway VARCHAR(50),
  gateway_response JSON,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
  FOREIGN KEY (buyer_id) REFERENCES buyers(buyer_id) ON DELETE CASCADE,
  INDEX idx_order (order_id),
  INDEX idx_buyer (buyer_id),
  INDEX idx_status (status),
  INDEX idx_created (created_at)
);

-- ====================================================================
-- 4. ORDER_TRACKING TABLE (New) - Live tracking for orders
-- ====================================================================
CREATE TABLE IF NOT EXISTS order_tracking (
  tracking_id INT PRIMARY KEY AUTO_INCREMENT,
  order_id INT NOT NULL,
  status ENUM('pending', 'accepted', 'packed', 'in_transit', 'delivered', 'cancelled') DEFAULT 'pending',
  latitude DECIMAL(10, 8),
  longitude DECIMAL(11, 8),
  delivery_boy_name VARCHAR(100),
  delivery_boy_phone VARCHAR(10),
  estimated_delivery_time DATETIME,
  actual_delivery_time DATETIME,
  notes TEXT,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
  UNIQUE KEY unique_tracking (order_id),
  INDEX idx_order (order_id),
  INDEX idx_status (status)
);

-- ====================================================================
-- 5. BUYER_REVIEWS TABLE (New) - Ratings and reviews from buyers
-- ====================================================================
CREATE TABLE IF NOT EXISTS buyer_reviews (
  review_id INT PRIMARY KEY AUTO_INCREMENT,
  order_id INT NOT NULL,
  buyer_id INT NOT NULL,
  product_id INT NOT NULL,
  farmer_id INT NOT NULL,
  product_rating INT CHECK (product_rating >= 1 AND product_rating <= 5),
  farmer_rating INT CHECK (farmer_rating >= 1 AND farmer_rating <= 5),
  product_review TEXT,
  farmer_review TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
  FOREIGN KEY (buyer_id) REFERENCES buyers(buyer_id) ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
  FOREIGN KEY (farmer_id) REFERENCES farmers(farmer_id) ON DELETE CASCADE,
  UNIQUE KEY unique_review (order_id),
  INDEX idx_buyer (buyer_id),
  INDEX idx_farmer (farmer_id),
  INDEX idx_product (product_id),
  INDEX idx_rating (product_rating)
);

-- ====================================================================
-- 6. RETURN_REQUESTS TABLE (New) - Handle returns and refunds
-- ====================================================================
CREATE TABLE IF NOT EXISTS return_requests (
  return_id INT PRIMARY KEY AUTO_INCREMENT,
  order_id INT NOT NULL,
  buyer_id INT NOT NULL,
  reason VARCHAR(255) NOT NULL,
  description TEXT,
  status ENUM('requested', 'approved', 'rejected', 'refunded') DEFAULT 'requested',
  refund_amount DECIMAL(10, 2),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
  FOREIGN KEY (buyer_id) REFERENCES buyers(buyer_id) ON DELETE CASCADE,
  INDEX idx_order (order_id),
  INDEX idx_buyer (buyer_id),
  INDEX idx_status (status)
);

-- ====================================================================
-- 7. BUYER_ADDRESSES TABLE (New) - Multiple delivery addresses
-- ====================================================================
CREATE TABLE IF NOT EXISTS buyer_addresses (
  address_id INT PRIMARY KEY AUTO_INCREMENT,
  buyer_id INT NOT NULL,
  type ENUM('home', 'work', 'other') DEFAULT 'home',
  address_line1 VARCHAR(255) NOT NULL,
  address_line2 VARCHAR(255),
  city VARCHAR(50) NOT NULL,
  state VARCHAR(50) NOT NULL,
  pincode VARCHAR(6) NOT NULL,
  latitude DECIMAL(10, 8),
  longitude DECIMAL(11, 8),
  is_default BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (buyer_id) REFERENCES buyers(buyer_id) ON DELETE CASCADE,
  INDEX idx_buyer (buyer_id),
  INDEX idx_pincode (pincode)
);

-- ====================================================================
-- ALTER ORDERS TABLE - Add buyer-specific columns
-- ====================================================================
ALTER TABLE orders ADD COLUMN buyer_id INT AFTER farmer_id;
ALTER TABLE orders ADD COLUMN delivery_address TEXT AFTER status;
ALTER TABLE orders ADD COLUMN buyer_phone VARCHAR(10) AFTER delivery_address;
ALTER TABLE orders ADD COLUMN buyer_location VARCHAR(100) AFTER buyer_phone;
ALTER TABLE orders ADD COLUMN payment_status ENUM('pending', 'completed', 'failed', 'refunded') DEFAULT 'pending' AFTER buyer_location;

ALTER TABLE orders ADD FOREIGN KEY (buyer_id) REFERENCES buyers(buyer_id) ON DELETE SET NULL;
ALTER TABLE orders ADD INDEX idx_buyer (buyer_id);
ALTER TABLE orders ADD INDEX idx_payment_status (payment_status);

-- ====================================================================
-- CREATE INDEXES FOR PERFORMANCE
-- ====================================================================

-- Buyers table indexes (location-based queries)
CREATE INDEX IF NOT EXISTS idx_buyers_location ON buyers(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_buyers_city ON buyers(city, state);

-- Cart indexes (fast queries)
CREATE INDEX IF NOT EXISTS idx_cart_farmer ON cart(farmer_id);

-- Payments indexes (payment tracking)
CREATE INDEX IF NOT EXISTS idx_payments_transaction ON payments(transaction_id);
CREATE INDEX IF NOT EXISTS idx_payments_method ON payments(payment_method);

-- Tracking indexes (real-time queries)
CREATE INDEX IF NOT EXISTS idx_tracking_updated ON order_tracking(updated_at);

-- Reviews indexes (aggregation queries)
CREATE INDEX IF NOT EXISTS idx_reviews_order ON buyer_reviews(order_id);
CREATE INDEX IF NOT EXISTS idx_reviews_created ON buyer_reviews(created_at);

-- Return indexes (return management)
CREATE INDEX IF NOT EXISTS idx_returns_created ON return_requests(created_at);

-- Addresses indexes (delivery lookups)
CREATE INDEX IF NOT EXISTS idx_addresses_default ON buyer_addresses(buyer_id, is_default);

-- ====================================================================
-- OTP VERIFICATION TABLE UPDATE (for buyers)
-- ====================================================================
-- Update otp_verification table to handle both farmers and buyers
ALTER TABLE otp_verification ADD COLUMN user_type ENUM('farmer', 'buyer') DEFAULT 'farmer';
CREATE INDEX IF NOT EXISTS idx_otp_user_type ON otp_verification(phone, user_type);

-- ====================================================================
-- SUMMARY STATISTICS
-- ====================================================================
/*
BUYER MODULE TABLES:
1. buyers (New) - 22 columns
2. cart (New) - 7 columns
3. payments (New) - 10 columns
4. order_tracking (New) - 11 columns
5. buyer_reviews (New) - 10 columns
6. return_requests (New) - 8 columns
7. buyer_addresses (New) - 11 columns

MODIFIED TABLES:
- orders: Added 5 columns (buyer_id, delivery_address, buyer_phone, buyer_location, payment_status)
- otp_verification: Added user_type column

TOTAL NEW COLUMNS: 79 columns
TOTAL NEW INDEXES: 15+ indexes
TOTAL NEW TABLES: 7

Total Database Now: 17 tables, comprehensive buyer-seller marketplace
*/

-- ====================================================================
-- TEST DATA (Optional - for development)
-- ====================================================================
-- Insert sample buyer for testing
INSERT INTO buyers (phone, email, first_name, last_name, password_hash, location, city, state, pincode)
VALUES (
  '9876543200',
  'buyer@example.com',
  'Ramesh',
  'Sharma',
  '$2b$12$abcdefghijklmnopqrstuvwxyz',
  'Hyderabad',
  'Hyderabad',
  'Telangana',
  '500001'
);

-- Insert sample delivery address
INSERT INTO buyer_addresses (buyer_id, type, address_line1, address_line2, city, state, pincode, is_default)
SELECT buyer_id, 'home', '123 Main Street', 'Apt 4', 'Hyderabad', 'Telangana', '500001', TRUE
FROM buyers WHERE phone = '9876543200';
