"""
Complete Models for Smart Farming Marketplace
PostgreSQL version using psycopg2 connection pool.
Includes: User, Farmer, Buyer, Admin, Product, Order, Payment, Review, etc.
"""

from datetime import datetime, timedelta
import json

# Global DB pool instance
_db_pool = None

def set_db_pool(pool):
    global _db_pool
    _db_pool = pool

def get_db_pool():
    global _db_pool
    if _db_pool is None:
        raise RuntimeError("Database pool not initialized")
    return _db_pool

# ============================================================================
# BASE MODEL CLASS
# ============================================================================
class BaseModel:
    """Base model with common database operations using psycopg2 connection pool"""
    
    @staticmethod
    def execute_query(query, params=None, fetch_one=False, fetch_all=False):
        """Execute query and return results (with auto-retry and pool recovery)"""
        import time as _time
        pool = get_db_pool()
        max_retries = 3
        
        for attempt in range(max_retries):
            conn = None
            cursor = None
            start = _time.time()
            try:
                conn = pool.getconn()
                
                # Test if connection is alive
                if conn.closed:
                    pool.putconn(conn, close=True)
                    conn = pool.getconn()
                
                # On retry attempts, validate the connection first
                if attempt > 0:
                    try:
                        test_cur = conn.cursor()
                        test_cur.execute('SELECT 1')
                        test_cur.close()
                    except Exception:
                        # Connection still bad — get a fresh one
                        try:
                            pool.putconn(conn, close=True)
                        except Exception:
                            pass
                        conn = pool.getconn()
                
                from psycopg2.extras import RealDictCursor
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                conn.commit()
                
                # Log slow queries (>1 second)
                elapsed = (_time.time() - start) * 1000
                if elapsed > 1000:
                    short_query = query.strip()[:80].replace('\n', ' ')
                    print(f"[SLOW-QUERY] {elapsed:.0f}ms: {short_query}...")
                
                if fetch_one:
                    result = cursor.fetchone()
                    return dict(result) if result else None
                elif fetch_all:
                    results = cursor.fetchall()
                    return [dict(row) for row in results] if results else []
                else:
                    return cursor.rowcount
            except (Exception,) as e:
                if conn:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                error_str = str(e).lower()
                # Retry on transient connection/timeout errors
                is_transient = (
                    'closed' in error_str or 
                    'connection' in error_str or 
                    'server closed' in error_str or
                    'terminating connection' in error_str or
                    'timeout' in error_str or
                    'ssl' in error_str or
                    'eof' in error_str
                )
                if attempt < max_retries - 1 and is_transient:
                    print(f"[DB-RETRY] Attempt {attempt + 1}/{max_retries} failed: {e}")
                    try:
                        if conn:
                            pool.putconn(conn, close=True)
                            conn = None
                    except Exception:
                        pass
                    _time.sleep(0.5 * (attempt + 1))  # Backoff: 0.5s, 1s
                    continue
                
                # All retries exhausted — try pool recreation as last resort
                if is_transient and attempt == max_retries - 1:
                    print(f"[DB-RECOVERY] All {max_retries} retries failed. Attempting pool recreation...")
                    try:
                        from app import recreate_db_pool
                        if recreate_db_pool():
                            print(f"[DB-RECOVERY] Pool recreated. Retrying query one final time...")
                            # One more attempt with the new pool
                            new_pool = get_db_pool()
                            final_conn = new_pool.getconn()
                            try:
                                final_cursor = final_conn.cursor(cursor_factory=RealDictCursor)
                                if params:
                                    final_cursor.execute(query, params)
                                else:
                                    final_cursor.execute(query)
                                final_conn.commit()
                                if fetch_one:
                                    result = final_cursor.fetchone()
                                    return dict(result) if result else None
                                elif fetch_all:
                                    results = final_cursor.fetchall()
                                    return [dict(row) for row in results] if results else []
                                else:
                                    return final_cursor.rowcount
                            finally:
                                try:
                                    final_cursor.close()
                                except Exception:
                                    pass
                                new_pool.putconn(final_conn)
                    except Exception as recovery_err:
                        print(f"[DB-RECOVERY] Recovery failed: {recovery_err}")
                
                print(f"[DB-ERROR] {e}")
                raise
            finally:
                if cursor:
                    try:
                        cursor.close()
                    except Exception:
                        pass
                if conn:
                    try:
                        pool.putconn(conn)
                    except Exception:
                        pass
    
    @staticmethod
    def execute_insert(query, params):
        """Execute insert and return last insert id using RETURNING clause"""
        pool = get_db_pool()
        conn = pool.getconn()
        try:
            from psycopg2.extras import RealDictCursor
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Add RETURNING id if not already present
            query_upper = query.strip().upper()
            if 'RETURNING' not in query_upper and query_upper.startswith('INSERT'):
                query = query.rstrip().rstrip(';') + ' RETURNING id'
            
            cursor.execute(query, params)
            conn.commit()
            
            result = cursor.fetchone()
            return result['id'] if result else None
        except Exception as e:
            conn.rollback()
            print(f"Insert error: {e}")
            raise
        finally:
            cursor.close()
            pool.putconn(conn)

# ============================================================================
# USER MODEL
# ============================================================================
class User(BaseModel):
    """User model - Base for all user types"""
    
    @staticmethod
    def create(username, email, phone, password_hash, first_name, last_name, role_id, firebase_uid=None):
        """Create new user"""
        query = """
        INSERT INTO users (username, email, phone, password_hash, first_name, last_name, role_id, firebase_uid)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        return User.execute_insert(query, (username, email, phone, password_hash, first_name, last_name, role_id, firebase_uid))
    
    @staticmethod
    def get_by_id(user_id):
        """Get user by ID"""
        query = """
        SELECT u.*, r.name as role_name 
        FROM users u
        LEFT JOIN roles r ON u.role_id = r.id
        WHERE u.id = %s
        """
        return User.execute_query(query, (user_id,), fetch_one=True)
    
    @staticmethod
    def get_by_email(email):
        """Get user by email"""
        query = """
        SELECT u.*, r.name as role_name 
        FROM users u
        LEFT JOIN roles r ON u.role_id = r.id
        WHERE u.email = %s
        """
        return User.execute_query(query, (email,), fetch_one=True)
    
    @staticmethod
    def get_by_phone(phone):
        """Get user by phone"""
        query = """
        SELECT u.*, r.name as role_name 
        FROM users u
        LEFT JOIN roles r ON u.role_id = r.id
        WHERE u.phone = %s
        """
        return User.execute_query(query, (phone,), fetch_one=True)
    
    @staticmethod
    def get_by_firebase_uid(firebase_uid):
        """Get user by Firebase UID"""
        query = """
        SELECT u.*, r.name as role_name 
        FROM users u
        LEFT JOIN roles r ON u.role_id = r.id
        WHERE u.firebase_uid = %s
        """
        return User.execute_query(query, (firebase_uid,), fetch_one=True)
    
    @staticmethod
    def update(user_id, **kwargs):
        """Update user fields"""
        allowed_fields = ['username', 'email', 'phone', 'first_name', 'last_name', 
                         'profile_image', 'status', 'is_verified', 'email_verified_at', 
                         'phone_verified_at', 'last_login', 'two_factor_enabled']
        
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not updates:
            return False
        
        set_clause = ', '.join([f"{k} = %s" for k in updates.keys()])
        values = list(updates.values()) + [user_id]
        
        query = f"UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
        return User.execute_query(query, values) > 0
    
    @staticmethod
    def verify_email(user_id):
        """Mark email as verified"""
        query = "UPDATE users SET is_verified = TRUE, email_verified_at = CURRENT_TIMESTAMP WHERE id = %s"
        return User.execute_query(query, (user_id,)) > 0
    
    @staticmethod
    def verify_phone(user_id):
        """Mark phone as verified"""
        query = "UPDATE users SET phone_verified_at = CURRENT_TIMESTAMP WHERE id = %s"
        return User.execute_query(query, (user_id,)) > 0
    
    @staticmethod
    def get_all_by_role(role_name, limit=50, offset=0):
        """Get all users by role"""
        query = """
        SELECT u.*, r.name as role_name 
        FROM users u
        LEFT JOIN roles r ON u.role_id = r.id
        WHERE r.name = %s
        ORDER BY u.created_at DESC
        LIMIT %s OFFSET %s
        """
        return User.execute_query(query, (role_name, limit, offset), fetch_all=True)

# ============================================================================
# FARMER MODEL
# ============================================================================
class Farmer(BaseModel):
    """Farmer model"""
    
    @staticmethod
    def create(user_id, location, latitude=None, longitude=None):
        """Create farmer profile"""
        query = """
        INSERT INTO farmers (user_id, location, latitude, longitude)
        VALUES (%s, %s, %s, %s)
        """
        return Farmer.execute_insert(query, (user_id, location, latitude, longitude))
    
    @staticmethod
    def get_by_user_id(user_id):
        """Get farmer by user ID"""
        query = """
        SELECT f.*
        FROM farmers f
        WHERE f.user_id = %s
        """
        return Farmer.execute_query(query, (user_id,), fetch_one=True)
    
    @staticmethod
    def get_by_id(farmer_id):
        """Get farmer by ID"""
        query = """
        SELECT f.*
        FROM farmers f
        WHERE f.id = %s
        """
        return Farmer.execute_query(query, (farmer_id,), fetch_one=True)
    
    @staticmethod
    def update(farmer_id, **kwargs):
        """Update farmer profile"""
        allowed_fields = ['aadhar_number', 'pan_number', 'bank_account', 'bank_ifsc', 
                         'bank_name', 'location', 'latitude', 'longitude', 'land_area_hectares',
                         'crops_grown', 'experience_years', 'certificate_image', 'is_verified',
                         'verification_date', 'verification_document', 'is_active']
        
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not updates:
            return False
        
        set_clause = ', '.join([f"{k} = %s" for k in updates.keys()])
        values = list(updates.values()) + [farmer_id]
        
        query = f"UPDATE farmers SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
        return Farmer.execute_query(query, values) > 0
    
    @staticmethod
    def verify_farmer(farmer_id):
        """Verify farmer"""
        query = """
        UPDATE farmers 
        SET is_verified = TRUE, verification_date = CURRENT_TIMESTAMP 
        WHERE id = %s
        """
        return Farmer.execute_query(query, (farmer_id,)) > 0
    
    @staticmethod
    def get_nearby_farmers(latitude, longitude, radius_km=10):
        """Get farmers near a location"""
        query = """
        SELECT f.*, u.first_name, u.last_name, u.email, u.phone,
               (3959 * acos(cos(radians(%s)) * cos(radians(latitude)) * 
               cos(radians(longitude) - radians(%s)) + sin(radians(%s)) * 
               sin(radians(latitude)))) AS distance
        FROM farmers f
        LEFT JOIN users u ON f.user_id = u.id
        WHERE f.is_active = TRUE AND f.is_verified = TRUE
          AND (3959 * acos(cos(radians(%s)) * cos(radians(latitude)) * 
               cos(radians(longitude) - radians(%s)) + sin(radians(%s)) * 
               sin(radians(latitude)))) < %s
        ORDER BY distance
        """
        return Farmer.execute_query(query, (latitude, longitude, latitude, latitude, longitude, latitude, radius_km), fetch_all=True)
    
    @staticmethod
    def get_farmer_stats(farmer_id):
        """Get farmer statistics"""
        query = """
        SELECT 
            f.id,
            COUNT(DISTINCT p.id) as total_products,
            COUNT(DISTINCT o.id) as total_orders,
            SUM(CASE WHEN o.status = 'delivered' THEN 1 ELSE 0 END) as delivered_orders,
            COALESCE(SUM(CASE WHEN o.status = 'delivered' THEN o.total_amount ELSE 0 END), 0) as total_earnings,
            COALESCE(AVG(CASE WHEN br.farmer_rating IS NOT NULL THEN br.farmer_rating ELSE NULL END), 0) as average_rating,
            COUNT(DISTINCT br.id) as total_ratings
        FROM farmers f
        LEFT JOIN products p ON f.id = p.farmer_id
        LEFT JOIN orders o ON f.id = o.farmer_id
        LEFT JOIN buyer_reviews br ON f.id = br.farmer_id
        WHERE f.id = %s
        GROUP BY f.id
        """
        return Farmer.execute_query(query, (farmer_id,), fetch_one=True)

# ============================================================================
# BUYER MODEL
# ============================================================================
class Buyer(BaseModel):
    """Buyer model"""
    
    @staticmethod
    def create(user_id, location, latitude=None, longitude=None):
        """Create buyer profile"""
        query = """
        INSERT INTO buyers (user_id, location, latitude, longitude)
        VALUES (%s, %s, %s, %s)
        """
        return Buyer.execute_insert(query, (user_id, location, latitude, longitude))
    
    @staticmethod
    def get_by_user_id(user_id):
        """Get buyer by user ID"""
        query = """
        SELECT b.*
        FROM buyers b
        WHERE b.user_id = %s
        """
        return Buyer.execute_query(query, (user_id,), fetch_one=True)
    
    @staticmethod
    def get_by_id(buyer_id):
        """Get buyer by ID"""
        query = """
        SELECT b.*
        FROM buyers b
        WHERE b.id = %s
        """
        return Buyer.execute_query(query, (buyer_id,), fetch_one=True)
    
    @staticmethod
    def update(buyer_id, **kwargs):
        """Update buyer profile"""
        allowed_fields = ['business_name', 'business_type', 'company_registration',
                         'location', 'latitude', 'longitude', 'delivery_address',
                         'gst_number', 'is_verified', 'is_active']
        
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not updates:
            return False
        
        set_clause = ', '.join([f"{k} = %s" for k in updates.keys()])
        values = list(updates.values()) + [buyer_id]
        
        query = f"UPDATE buyers SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
        return Buyer.execute_query(query, values) > 0
    
    @staticmethod
    def get_buyer_stats(buyer_id):
        """Get buyer statistics"""
        query = """
        SELECT 
            b.id,
            COUNT(DISTINCT o.id) as total_orders,
            COALESCE(SUM(CASE WHEN o.status = 'delivered' THEN o.total_amount ELSE 0 END), 0) as total_spent,
            COALESCE(AVG(CASE WHEN br.product_rating IS NOT NULL THEN br.product_rating ELSE NULL END), 0) as average_rating,
            COUNT(DISTINCT br.id) as total_reviews
        FROM buyers b
        LEFT JOIN orders o ON b.id = o.buyer_id
        LEFT JOIN buyer_reviews br ON b.id = br.buyer_id
        WHERE b.id = %s
        GROUP BY b.id
        """
        return Buyer.execute_query(query, (buyer_id,), fetch_one=True)

# ============================================================================
# PRODUCT MODEL
# ============================================================================
class Product(BaseModel):
    """Product model"""
    
    @staticmethod
    def create(farmer_id, category_id, name, slug, description, quantity, unit, price, location):
        """Create product"""
        query = """
        INSERT INTO products (farmer_id, category, name, slug, description, quantity, unit, price, location, is_available)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
        """
        return Product.execute_insert(query, (farmer_id, category_id, name, slug, description, quantity, unit, price, location))
    
    @staticmethod
    def get_by_id(product_id):
        """Get product by ID"""
        query = """
        SELECT p.*, f.first_name as farmer_first_name, f.last_name as farmer_last_name, 
               f.email as farmer_email, f.phone as farmer_phone
        FROM products p
        LEFT JOIN farmers f ON p.farmer_id = f.id
        WHERE p.id = %s
        """
        return Product.execute_query(query, (product_id,), fetch_one=True)
    
    @staticmethod
    def get_by_slug(slug):
        """Get product by slug"""
        query = """
        SELECT p.*, f.first_name as farmer_first_name, f.last_name as farmer_last_name
        FROM products p
        LEFT JOIN farmers f ON p.farmer_id = f.id
        WHERE p.slug = %s
        """
        return Product.execute_query(query, (slug,), fetch_one=True)
    
    @staticmethod
    def get_by_farmer(farmer_id, limit=50, offset=0):
        """Get products by farmer"""
        query = """
        SELECT p.*
        FROM products p
        WHERE p.farmer_id = %s
        ORDER BY p.created_at DESC
        LIMIT %s OFFSET %s
        """
        return Product.execute_query(query, (farmer_id, limit, offset), fetch_all=True)
    
    @staticmethod
    def search(search_term, category_id=None, limit=50, offset=0):
        """Search products"""
        query = """
        SELECT p.*
        FROM products p
        WHERE p.is_available = TRUE AND (p.name ILIKE %s OR p.description ILIKE %s)
        """
        params = [f"%{search_term}%", f"%{search_term}%"]
        
        if category_id:
            query += " AND p.category = %s"
            params.append(category_id)
        
        query += " ORDER BY p.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        return Product.execute_query(query, params, fetch_all=True)
    
    @staticmethod
    def update(product_id, **kwargs):
        """Update product"""
        allowed_fields = ['name', 'slug', 'description', 'detailed_description',
                         'quantity', 'unit', 'price', 'min_order_quantity',
                         'max_order_quantity', 'discount_percentage', 'location',
                         'harvest_date', 'expiry_date', 'images', 'specifications',
                         'certifications', 'is_organic', 'is_available']
        
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not updates:
            return False
        
        set_clause = ', '.join([f"{k} = %s" for k in updates.keys()])
        values = list(updates.values()) + [product_id]
        
        query = f"UPDATE products SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
        return Product.execute_query(query, values) > 0
    
    @staticmethod
    def increment_views(product_id):
        """Increment product views"""
        query = "UPDATE products SET views_count = COALESCE(views_count, 0) + 1 WHERE id = %s"
        return Product.execute_query(query, (product_id,)) > 0
    
    @staticmethod
    def get_featured_products(limit=10):
        """Get featured products"""
        query = """
        SELECT p.*
        FROM products p
        WHERE p.is_available = TRUE
        ORDER BY p.average_rating DESC NULLS LAST
        LIMIT %s
        """
        return Product.execute_query(query, (limit,), fetch_all=True)

# ============================================================================
# ORDER MODEL
# ============================================================================
class Order(BaseModel):
    """Order model"""
    
    @staticmethod
    def create(order_number, farmer_id, buyer_id, product_id, quantity, unit_price, 
               total_price, final_price, delivery_address):
        """Create order"""
        query = """
        INSERT INTO orders (order_number, farmer_id, buyer_id, product_id, quantity, 
                           total_amount, delivery_address, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending')
        """
        return Order.execute_insert(query, (order_number, farmer_id, buyer_id, product_id, 
                                           quantity, total_price, delivery_address))
    
    @staticmethod
    def get_by_id(order_id):
        """Get order by ID"""
        query = """
        SELECT o.*, p.name as product_name,
               fu.first_name as farmer_first_name, fu.last_name as farmer_last_name,
               bu.first_name as buyer_first_name, bu.last_name as buyer_last_name
        FROM orders o
        LEFT JOIN products p ON o.product_id = p.id
        LEFT JOIN farmers f ON o.farmer_id = f.id
        LEFT JOIN users fu ON f.user_id = fu.id
        LEFT JOIN buyers b ON o.buyer_id = b.id
        LEFT JOIN users bu ON b.user_id = bu.id
        WHERE o.id = %s
        """
        return Order.execute_query(query, (order_id,), fetch_one=True)
    
    @staticmethod
    def get_farmer_orders(farmer_id, status=None, limit=50, offset=0):
        """Get orders for farmer"""
        query = """
        SELECT o.*, o.total_amount as total, p.name as product_name,
               CONCAT(b.first_name, ' ', b.last_name) as buyer_name,
               b.phone as buyer_phone, b.email as buyer_email,
               b.location as buyer_address, b.city as buyer_city,
               b.state as buyer_state, b.pincode as buyer_pincode,
               b.first_name as buyer_first_name, b.last_name as buyer_last_name
        FROM orders o
        LEFT JOIN products p ON o.product_id = p.id
        LEFT JOIN buyers b ON o.buyer_id = b.id
        WHERE o.farmer_id = %s
        """
        params = [farmer_id]
        
        if status:
            query += " AND o.status = %s"
            params.append(status)
        
        query += " ORDER BY o.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        return Order.execute_query(query, params, fetch_all=True)
    
    @staticmethod
    def get_buyer_orders(buyer_id, status=None, limit=50, offset=0):
        """Get orders for buyer"""
        query = """
        SELECT o.*, p.name as product_name,
               f.first_name as farmer_first_name, f.last_name as farmer_last_name, f.phone as farmer_phone
        FROM orders o
        LEFT JOIN products p ON o.product_id = p.id
        LEFT JOIN farmers f ON o.farmer_id = f.id
        WHERE o.buyer_id = %s
        """
        params = [buyer_id]
        
        if status:
            query += " AND o.status = %s"
            params.append(status)
        
        query += " ORDER BY o.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        return Order.execute_query(query, params, fetch_all=True)
    
    @staticmethod
    def update_status(order_id, status):
        """Update order status"""
        query = "UPDATE orders SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
        return Order.execute_query(query, (status, order_id)) > 0
    
    @staticmethod
    def update_payment_status(order_id, payment_status):
        """Update order payment status"""
        query = "UPDATE orders SET payment_status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
        return Order.execute_query(query, (payment_status, order_id)) > 0

# ============================================================================
# PAYMENT MODEL
# ============================================================================
class Payment(BaseModel):
    """Payment model"""
    
    @staticmethod
    def create(order_id, buyer_id, amount, payment_method):
        """Create payment"""
        query = """
        INSERT INTO payments (order_id, buyer_id, amount, payment_method, status)
        VALUES (%s, %s, %s, %s, 'pending')
        """
        return Payment.execute_insert(query, (order_id, buyer_id, amount, payment_method))
    
    @staticmethod
    def get_by_id(payment_id):
        """Get payment by ID"""
        query = "SELECT * FROM payments WHERE id = %s"
        return Payment.execute_query(query, (payment_id,), fetch_one=True)
    
    @staticmethod
    def get_by_order(order_id):
        """Get payment by order"""
        query = "SELECT * FROM payments WHERE order_id = %s"
        return Payment.execute_query(query, (order_id,), fetch_one=True)
    
    @staticmethod
    def update_with_razorpay(payment_id, razorpay_payment_id, razorpay_order_id, razorpay_signature):
        """Update payment with Razorpay details"""
        query = """
        UPDATE payments 
        SET razorpay_payment_id = %s, razorpay_order_id = %s, razorpay_signature = %s,
            transaction_id = %s, status = 'completed', payment_date = CURRENT_TIMESTAMP
        WHERE id = %s
        """
        return Payment.execute_query(query, (razorpay_payment_id, razorpay_order_id, 
                                            razorpay_signature, razorpay_payment_id, payment_id)) > 0
    
    @staticmethod
    def mark_failed(payment_id, error_message):
        """Mark payment as failed"""
        query = """
        UPDATE payments 
        SET status = 'failed', error_message = %s
        WHERE id = %s
        """
        return Payment.execute_query(query, (error_message, payment_id)) > 0

# ============================================================================
# REVIEW MODEL
# ============================================================================
class Review(BaseModel):
    """Review model"""
    
    @staticmethod
    def create(product_id, buyer_id, rating, comment, order_id=None):
        """Create review"""
        query = """
        INSERT INTO buyer_reviews (product_id, order_id, buyer_id, product_rating, product_review, farmer_id)
        SELECT %s, %s, %s, %s, %s, p.farmer_id FROM products p WHERE p.id = %s
        """
        return Review.execute_insert(query, (product_id, order_id, buyer_id, rating, comment, product_id))
    
    @staticmethod
    def get_product_reviews(product_id, limit=20, offset=0):
        """Get reviews for product"""
        query = """
        SELECT br.*, b.first_name, b.last_name
        FROM buyer_reviews br
        LEFT JOIN buyers b ON br.buyer_id = b.id
        WHERE br.product_id = %s
        ORDER BY br.created_at DESC
        LIMIT %s OFFSET %s
        """
        return Review.execute_query(query, (product_id, limit, offset), fetch_all=True)
    
    @staticmethod
    def approve_review(review_id):
        """Approve review — no-op since buyer_reviews doesn't have is_approved"""
        return True

# ============================================================================
# MESSAGE MODEL
# ============================================================================
class Message(BaseModel):
    """Message model"""
    
    @staticmethod
    def create(conversation_id, sender_id, receiver_id, content, attachment_url=None):
        """Create message"""
        query = """
        INSERT INTO messages (conversation_id, sender_id, receiver_id, content, attachment_url)
        VALUES (%s, %s, %s, %s, %s)
        """
        return Message.execute_insert(query, (conversation_id, sender_id, receiver_id, content, attachment_url))
    
    @staticmethod
    def get_conversation_messages(conversation_id, limit=50, offset=0):
        """Get messages in conversation"""
        query = """
        SELECT m.*
        FROM messages m
        WHERE m.conversation_id = %s
        ORDER BY m.created_at DESC
        LIMIT %s OFFSET %s
        """
        return Message.execute_query(query, (conversation_id, limit, offset), fetch_all=True)
    
    @staticmethod
    def mark_as_read(message_id):
        """Mark message as read"""
        query = "UPDATE messages SET is_read = TRUE, read_at = CURRENT_TIMESTAMP WHERE id = %s"
        return Message.execute_query(query, (message_id,)) > 0

# ============================================================================
# NOTIFICATION MODEL
# ============================================================================
class Notification(BaseModel):
    """Notification model"""
    
    @staticmethod
    def create(user_id, title, message, notification_type, data=None, action_url=None):
        """Create notification"""
        query = """
        INSERT INTO notifications (user_id, title, message, type, data, action_url)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        data_json = json.dumps(data) if data else None
        return Notification.execute_insert(query, (user_id, title, message, notification_type, data_json, action_url))
    
    @staticmethod
    def get_user_notifications(user_id, limit=20, offset=0):
        """Get user notifications"""
        query = """
        SELECT * FROM notifications
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """
        return Notification.execute_query(query, (user_id, limit, offset), fetch_all=True)
    
    @staticmethod
    def mark_as_read(notification_id):
        """Mark notification as read"""
        query = "UPDATE notifications SET is_read = TRUE, read_at = CURRENT_TIMESTAMP WHERE id = %s"
        return Notification.execute_query(query, (notification_id,)) > 0

# ============================================================================
# OTP MODEL
# ============================================================================
class OTP(BaseModel):
    """OTP model"""
    
    @staticmethod
    def create(email=None, phone=None, otp_code=None, purpose='registration'):
        """Create OTP"""
        expires_at = datetime.now() + timedelta(minutes=10)
        query = """
        INSERT INTO otps (email, phone, otp, purpose, expires_at)
        VALUES (%s, %s, %s, %s, %s)
        """
        return OTP.execute_insert(query, (email, phone, otp_code, purpose, expires_at))
    
    @staticmethod
    def verify(email=None, phone=None, otp_code=None):
        """Verify OTP"""
        if email:
            query = """
            SELECT * FROM otps 
            WHERE email = %s AND otp = %s AND expires_at > NOW() AND is_verified = FALSE
            ORDER BY created_at DESC LIMIT 1
            """
            return OTP.execute_query(query, (email, otp_code), fetch_one=True)
        else:
            query = """
            SELECT * FROM otps 
            WHERE phone = %s AND otp = %s AND expires_at > NOW() AND is_verified = FALSE
            ORDER BY created_at DESC LIMIT 1
            """
            return OTP.execute_query(query, (phone, otp_code), fetch_one=True)
    
    @staticmethod
    def mark_verified(otp_id):
        """Mark OTP as verified"""
        query = """
        UPDATE otps 
        SET is_verified = TRUE 
        WHERE id = %s
        """
        return OTP.execute_query(query, (otp_id,)) > 0
    
    @staticmethod
    def increment_attempts(otp_id):
        """Increment OTP attempts"""
        query = "UPDATE otps SET attempts = attempts + 1 WHERE id = %s"
        return OTP.execute_query(query, (otp_id,)) > 0

# ============================================================================
# CART MODEL
# ============================================================================
class Cart(BaseModel):
    """Cart model"""
    
    @staticmethod
    def create(buyer_id):
        """Create cart for buyer"""
        query = "INSERT INTO cart (buyer_id, product_id, quantity) VALUES (%s, 0, 0)"
        return Cart.execute_insert(query, (buyer_id,))
    
    @staticmethod
    def get_or_create(buyer_id):
        """Get cart items for buyer"""
        query = "SELECT * FROM cart WHERE buyer_id = %s AND is_active = TRUE"
        return Cart.execute_query(query, (buyer_id,), fetch_all=True) or []
    
    @staticmethod
    def add_item(cart_id, product_id, quantity=1):
        """Add item to cart (cart_id is actually buyer_id here)"""
        # Use ON CONFLICT for PostgreSQL upsert
        query = """
        INSERT INTO cart (buyer_id, product_id, quantity)
        VALUES (%s, %s, %s)
        ON CONFLICT (buyer_id, product_id) 
        DO UPDATE SET quantity = cart.quantity + EXCLUDED.quantity
        """
        return Cart.execute_insert(query, (cart_id, product_id, quantity))
    
    @staticmethod
    def get_items(cart_id, limit=100):
        """Get cart items"""
        query = """
        SELECT c.*, p.name, p.price, p.images, p.farmer_id
        FROM cart c
        LEFT JOIN products p ON c.product_id = p.id
        WHERE c.buyer_id = %s AND c.is_active = TRUE
        LIMIT %s
        """
        return Cart.execute_query(query, (cart_id, limit), fetch_all=True)
    
    @staticmethod
    def remove_item(cart_item_id):
        """Remove item from cart"""
        query = "DELETE FROM cart WHERE id = %s"
        return Cart.execute_query(query, (cart_item_id,)) > 0
    
    @staticmethod
    def clear_cart(cart_id):
        """Clear all items from cart (cart_id = buyer_id)"""
        query = "DELETE FROM cart WHERE buyer_id = %s"
        return Cart.execute_query(query, (cart_id,)) > 0

# ============================================================================
# WALLET MODEL
# ============================================================================
class Wallet(BaseModel):
    """Wallet model"""
    
    @staticmethod
    def create(user_id):
        """Create wallet for user"""
        query = "INSERT INTO wallet (farmer_id, balance) VALUES (%s, 0)"
        return Wallet.execute_insert(query, (user_id,))
    
    @staticmethod
    def get(user_id):
        """Get wallet"""
        query = "SELECT * FROM wallet WHERE farmer_id = %s"
        return Wallet.execute_query(query, (user_id,), fetch_one=True)
    
    @staticmethod
    def add_balance(user_id, amount):
        """Add balance to wallet"""
        query = """
        UPDATE wallet 
        SET balance = balance + %s, total_earnings = total_earnings + %s
        WHERE farmer_id = %s
        """
        return Wallet.execute_query(query, (amount, amount, user_id)) > 0
    
    @staticmethod
    def deduct_balance(user_id, amount):
        """Deduct balance from wallet"""
        query = """
        UPDATE wallet 
        SET balance = balance - %s
        WHERE farmer_id = %s AND balance >= %s
        """
        return Wallet.execute_query(query, (amount, user_id, amount)) > 0

# ============================================================================
# CONVERSATION MODEL
# ============================================================================
class Conversation(BaseModel):
    """Conversation model"""
    
    @staticmethod
    def get_or_create(user_1_id, user_2_id):
        """Get or create conversation between two users"""
        # Ensure smaller ID comes first
        if user_1_id > user_2_id:
            user_1_id, user_2_id = user_2_id, user_1_id
        
        query = "SELECT * FROM conversations WHERE user_1_id = %s AND user_2_id = %s"
        conv = Conversation.execute_query(query, (user_1_id, user_2_id), fetch_one=True)
        
        if conv:
            return conv
        
        insert_query = "INSERT INTO conversations (user_1_id, user_2_id) VALUES (%s, %s)"
        conv_id = Conversation.execute_insert(insert_query, (user_1_id, user_2_id))
        
        return Conversation.execute_query(query, (user_1_id, user_2_id), fetch_one=True)

# Admin model for admin-specific operations
class Admin(BaseModel):
    """Admin model"""
    
    @staticmethod
    def get_by_user_id(user_id):
        """Get admin by user ID"""
        query = "SELECT * FROM admins WHERE user_id = %s"
        return Admin.execute_query(query, (user_id,), fetch_one=True)

# ============================================================================
# TRANSACTION MODEL
# ============================================================================
class Transaction(BaseModel):
    """Transaction model for payment/earning records"""
    
    @staticmethod
    def create(user_id, type, amount, order_id=None, payment_id=None, status='completed'):
        """Create transaction record"""
        query = """
        INSERT INTO wallet (farmer_id, balance, total_earnings)
        VALUES (%s, %s, %s)
        ON CONFLICT (farmer_id) 
        DO UPDATE SET balance = wallet.balance + EXCLUDED.balance, 
                      total_earnings = wallet.total_earnings + EXCLUDED.total_earnings
        """
        try:
            return Transaction.execute_query(query, (user_id, amount, amount))
        except Exception:
            return None
    
    @staticmethod
    def get_by_user(user_id, limit=20, offset=0):
        """Get transactions for user"""
        query = "SELECT * FROM payments WHERE buyer_id = %s ORDER BY created_at DESC LIMIT %s OFFSET %s"
        return Transaction.execute_query(query, (user_id, limit, offset), fetch_all=True) or []
