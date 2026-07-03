"""
Checkout & Payment Router - Complete Zomato-like order flow
Handles: Checkout, Razorpay payments, COD, order tracking, farmer orders, wallet
"""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from utils.jwt_utils import get_current_user
from models.models import BaseModel
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import json
import random
import hmac
import hashlib

load_dotenv()

# ---------------------------------------------------------------------------
# Razorpay client (reuse from env)
# ---------------------------------------------------------------------------
razorpay_client = None
try:
    import razorpay
    rz_key = os.getenv('RAZORPAY_KEY_ID')
    rz_secret = os.getenv('RAZORPAY_KEY_SECRET')
    if rz_key and rz_secret:
        razorpay_client = razorpay.Client(auth=(rz_key, rz_secret))
        print("[OK] Checkout: Razorpay configured")
    else:
        print("[SKIP] Checkout: Razorpay keys not set")
except ImportError:
    print("[SKIP] Checkout: razorpay not installed")

RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', '')

# ---------------------------------------------------------------------------
# Stripe client (for card payments & subscriptions)
# ---------------------------------------------------------------------------
stripe_client = None
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_KEY', os.getenv('STRIPE_PUBLISHABLE_KEY', ''))
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET', '')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
try:
    import stripe
    if STRIPE_SECRET_KEY:
        stripe.api_key = STRIPE_SECRET_KEY
        stripe_client = stripe
        print(f"[OK] Checkout: Stripe configured (key: {STRIPE_PUBLISHABLE_KEY[:12]}...)")
    else:
        print("[SKIP] Checkout: Stripe keys not set")
except ImportError:
    print("[SKIP] Checkout: stripe not installed")

# ---------------------------------------------------------------------------
# Platform config
# ---------------------------------------------------------------------------
PLATFORM_FEE_PERCENT = 2.0   # 2% platform commission
DELIVERY_FEE_BASE = 40       # Base delivery fee ₹40
DELIVERY_FEE_PER_KM = 5      # ₹5 per km (simplified)
FREE_DELIVERY_THRESHOLD = 500  # Free delivery above ₹500

checkout_router = APIRouter(prefix='/api/checkout', tags=['Checkout'])

# ============================================================================
# DB MIGRATION — Create tables if they don't exist
# ============================================================================

def run_checkout_migration():
    """Create checkout tables on startup"""
    queries = [
        """CREATE TABLE IF NOT EXISTS checkout_orders (
            id SERIAL PRIMARY KEY,
            order_number VARCHAR(30) UNIQUE NOT NULL,
            buyer_id INTEGER NOT NULL,
            farmer_id INTEGER,
            subtotal DECIMAL(12,2) DEFAULT 0,
            delivery_fee DECIMAL(10,2) DEFAULT 0,
            platform_fee DECIMAL(10,2) DEFAULT 0,
            total_amount DECIMAL(12,2) DEFAULT 0,
            payment_method VARCHAR(20) DEFAULT 'cod',
            payment_status VARCHAR(20) DEFAULT 'PENDING',
            order_status VARCHAR(30) DEFAULT 'PLACED',
            razorpay_order_id VARCHAR(100),
            razorpay_payment_id VARCHAR(100),
            razorpay_signature VARCHAR(255),
            delivery_address TEXT,
            buyer_name VARCHAR(100),
            buyer_phone VARCHAR(20),
            buyer_email VARCHAR(100),
            notes TEXT,
            estimated_delivery TIMESTAMP,
            delivered_at TIMESTAMP,
            cancelled_at TIMESTAMP,
            cancel_reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS checkout_order_items (
            id SERIAL PRIMARY KEY,
            order_id INTEGER REFERENCES checkout_orders(id) ON DELETE CASCADE,
            product_id INTEGER NOT NULL,
            product_name VARCHAR(200),
            product_image TEXT,
            quantity INTEGER DEFAULT 1,
            unit_price DECIMAL(10,2) DEFAULT 0,
            total_price DECIMAL(12,2) DEFAULT 0,
            farmer_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS checkout_payments (
            id SERIAL PRIMARY KEY,
            order_id INTEGER REFERENCES checkout_orders(id) ON DELETE CASCADE,
            transaction_id VARCHAR(50) UNIQUE,
            payment_method VARCHAR(30),
            payment_gateway VARCHAR(30) DEFAULT 'razorpay',
            amount DECIMAL(12,2) DEFAULT 0,
            currency VARCHAR(5) DEFAULT 'INR',
            status VARCHAR(20) DEFAULT 'PENDING',
            razorpay_order_id VARCHAR(100),
            razorpay_payment_id VARCHAR(100),
            razorpay_signature VARCHAR(255),
            gateway_response TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS farmer_wallets (
            id SERIAL PRIMARY KEY,
            farmer_id INTEGER UNIQUE NOT NULL,
            available_balance DECIMAL(12,2) DEFAULT 0,
            total_earnings DECIMAL(12,2) DEFAULT 0,
            total_commission DECIMAL(12,2) DEFAULT 0,
            pending_settlement DECIMAL(12,2) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS wallet_transactions (
            id SERIAL PRIMARY KEY,
            farmer_id INTEGER NOT NULL,
            order_id INTEGER,
            type VARCHAR(20) DEFAULT 'credit',
            amount DECIMAL(12,2) DEFAULT 0,
            commission DECIMAL(10,2) DEFAULT 0,
            net_amount DECIMAL(12,2) DEFAULT 0,
            description TEXT,
            balance_after DECIMAL(12,2) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS order_status_history (
            id SERIAL PRIMARY KEY,
            order_id INTEGER NOT NULL,
            status VARCHAR(30) NOT NULL,
            description TEXT,
            updated_by VARCHAR(20) DEFAULT 'system',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS delivery_addresses (
            id SERIAL PRIMARY KEY,
            buyer_id INTEGER NOT NULL,
            label VARCHAR(50) DEFAULT 'Home',
            full_name VARCHAR(100),
            phone VARCHAR(20),
            address_line1 TEXT NOT NULL,
            address_line2 TEXT,
            city VARCHAR(100),
            state VARCHAR(100),
            pincode VARCHAR(10),
            landmark TEXT,
            is_default BOOLEAN DEFAULT FALSE,
            latitude DECIMAL(10,7),
            longitude DECIMAL(10,7),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""
    ]
    
    for q in queries:
        try:
            BaseModel.execute_query(q)
        except Exception as e:
            print(f"[WARN] Checkout migration: {e}")
    
    print("[OK] Checkout tables ready")


# ============================================================================
# HELPERS
# ============================================================================

def _generate_order_number():
    """Generate unique order number: SF-YYYYMMDD-XXXX"""
    date = datetime.now().strftime('%Y%m%d')
    rand = random.randint(1000, 9999)
    return f"SF-{date}-{rand}"

def _generate_txn_id():
    """Generate unique transaction ID"""
    ts = datetime.now().strftime('%Y%m%d%H%M%S')
    rand = random.randint(1000, 9999)
    return f"TXN-{ts}-{rand}"

def _calculate_delivery_fee(subtotal):
    """Calculate delivery fee based on order value"""
    if subtotal >= FREE_DELIVERY_THRESHOLD:
        return 0
    return DELIVERY_FEE_BASE

def _calculate_platform_fee(subtotal):
    """Calculate platform commission"""
    return round(subtotal * PLATFORM_FEE_PERCENT / 100, 2)

def _serialize_dt(row):
    """Convert datetime objects to ISO strings"""
    if not row:
        return row
    out = {}
    for k, v in row.items():
        if isinstance(v, datetime):
            out[k] = v.isoformat()
        elif hasattr(v, '__str__') and not isinstance(v, (str, int, float, bool, type(None))):
            out[k] = str(v)
        else:
            out[k] = v
    return out

def _add_status_history(order_id, status, description='', updated_by='system'):
    """Add entry to order status history"""
    try:
        BaseModel.execute_query(
            """INSERT INTO order_status_history (order_id, status, description, updated_by)
               VALUES (%s, %s, %s, %s)""",
            (order_id, status, description, updated_by)
        )
    except Exception as e:
        print(f"Status history error: {e}")

def _credit_farmer_wallet(farmer_id, order_id, order_amount, platform_fee):
    """Credit farmer wallet after successful delivery"""
    net_amount = float(order_amount) - float(platform_fee)
    
    # Upsert wallet
    wallet = BaseModel.execute_query(
        "SELECT * FROM farmer_wallets WHERE farmer_id = %s",
        (farmer_id,), fetch_one=True
    )
    
    if wallet:
        BaseModel.execute_query(
            """UPDATE farmer_wallets 
               SET available_balance = available_balance + %s,
                   total_earnings = total_earnings + %s,
                   total_commission = total_commission + %s,
                   updated_at = NOW()
               WHERE farmer_id = %s""",
            (net_amount, net_amount, float(platform_fee), farmer_id)
        )
        new_balance = float(wallet['available_balance']) + net_amount
    else:
        BaseModel.execute_query(
            """INSERT INTO farmer_wallets (farmer_id, available_balance, total_earnings, total_commission)
               VALUES (%s, %s, %s, %s)""",
            (farmer_id, net_amount, net_amount, float(platform_fee))
        )
        new_balance = net_amount
    
    # Record transaction
    BaseModel.execute_query(
        """INSERT INTO wallet_transactions 
           (farmer_id, order_id, type, amount, commission, net_amount, description, balance_after)
           VALUES (%s, %s, 'credit', %s, %s, %s, %s, %s)""",
        (farmer_id, order_id, float(order_amount), float(platform_fee), net_amount,
         f"Payment for order #{order_id}", new_balance)
    )


# ============================================================================
# 1. CALCULATE ORDER TOTAL
# ============================================================================

@checkout_router.post('/calculate')
async def calculate_order(request: Request, user_id: str = Depends(get_current_user)):
    """Calculate order total with breakdown"""
    try:
        data = await request.json()
        items = data.get('items', [])
        
        if not items:
            return JSONResponse(status_code=400, content={'error': 'No items provided'})
        
        subtotal = 0
        item_details = []
        
        for item in items:
            product_id = item.get('product_id')
            quantity = int(item.get('quantity', 1))
            
            product = BaseModel.execute_query(
                "SELECT id, name, price, unit, images FROM products WHERE id = %s",
                (product_id,), fetch_one=True
            )
            
            if not product:
                continue
            
            price = float(product['price'])
            total = price * quantity
            subtotal += total
            
            images = []
            if product.get('images'):
                try:
                    images = json.loads(product['images']) if isinstance(product['images'], str) else product['images']
                except:
                    images = []
            
            item_details.append({
                'product_id': product['id'],
                'name': product['name'],
                'price': price,
                'quantity': quantity,
                'total': total,
                'unit': product.get('unit', 'kg'),
                'image': images[0] if images else '',
            })
        
        delivery_fee = _calculate_delivery_fee(subtotal)
        platform_fee = _calculate_platform_fee(subtotal)
        total = subtotal + delivery_fee
        
        return JSONResponse(content={
            'success': True,
            'items': item_details,
            'subtotal': subtotal,
            'delivery_fee': delivery_fee,
            'platform_fee': platform_fee,
            'total_amount': total,
            'free_delivery_threshold': FREE_DELIVERY_THRESHOLD,
            'currency': 'INR'
        })
    except Exception as e:
        print(f"Calculate error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})


# ============================================================================
# 2. CREATE ORDER
# ============================================================================

@checkout_router.post('/create-order')
async def create_order(request: Request, user_id: str = Depends(get_current_user)):
    """Create order — COD or Online"""
    try:
        data = await request.json()
        print(f"[CHECKOUT PAYLOAD] {data}")
        items = data.get('items', [])
        payment_method = data.get('payment_method', 'cod')  # 'cod' or 'online'
        delivery_address = data.get('delivery_address', '')
        buyer_name = data.get('buyer_name', '')
        buyer_phone = data.get('buyer_phone', '')
        buyer_email = data.get('buyer_email', '')
        notes = data.get('notes', '')
        
        if not items:
            return JSONResponse(status_code=400, content={'error': 'No items in order'})
        if not delivery_address:
            return JSONResponse(status_code=400, content={'error': 'Delivery address required'})
        
        # Calculate totals
        subtotal = 0
        farmer_id = None
        order_items = []
        
        for item in items:
            product = BaseModel.execute_query(
                "SELECT id, name, price, farmer_id, images FROM products WHERE id = %s",
                (item.get('product_id'),), fetch_one=True
            )
            if not product:
                continue
            
            price = float(product['price'])
            qty = int(item.get('quantity', 1))
            total = price * qty
            subtotal += total
            
            if not farmer_id:
                farmer_id = product.get('farmer_id')
            
            images = []
            if product.get('images'):
                try:
                    images = json.loads(product['images']) if isinstance(product['images'], str) else product['images']
                except:
                    images = []
            
            order_items.append({
                'product_id': product['id'],
                'product_name': product['name'],
                'product_image': images[0] if images else '',
                'quantity': qty,
                'unit_price': price,
                'total_price': total,
                'farmer_id': product.get('farmer_id'),
            })
        
        delivery_fee = float(data.get('delivery_fee', _calculate_delivery_fee(subtotal)))
        platform_fee = float(data.get('platform_fee', _calculate_platform_fee(subtotal)))
        total_amount = float(data.get('total_amount', subtotal + delivery_fee))
        
        order_number = _generate_order_number()
        
        # Set initial statuses based on payment method
        if payment_method == 'cod':
            payment_status = 'PENDING'
            order_status = 'CONFIRMED'
        else:
            payment_status = 'PENDING'
            order_status = 'PLACED'
        
        estimated_delivery = datetime.now() + timedelta(days=2)
        
        # Insert order
        order_id = BaseModel.execute_query(
            """INSERT INTO checkout_orders 
               (order_number, buyer_id, farmer_id, subtotal, delivery_fee, platform_fee,
                total_amount, payment_method, payment_status, order_status,
                delivery_address, buyer_name, buyer_phone, buyer_email, notes, estimated_delivery)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               RETURNING id""",
            (order_number, int(user_id), farmer_id, subtotal, delivery_fee, platform_fee,
             total_amount, payment_method, payment_status, order_status,
             delivery_address, buyer_name, buyer_phone, buyer_email, notes, estimated_delivery),
            fetch_one=True
        )
        
        oid = order_id['id'] if order_id else None
        
        if not oid:
            return JSONResponse(status_code=500, content={'error': 'Failed to create order'})
        
        # Insert order items
        for oi in order_items:
            BaseModel.execute_query(
                """INSERT INTO checkout_order_items 
                   (order_id, product_id, product_name, product_image, quantity, unit_price, total_price, farmer_id)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (oid, oi['product_id'], oi['product_name'], oi['product_image'],
                 oi['quantity'], oi['unit_price'], oi['total_price'], oi['farmer_id'])
            )
        
        # Add status history
        _add_status_history(oid, order_status, f'Order placed via {payment_method.upper()}', 'buyer')

        # Get farmer details for dynamic split routing
        farmer_name = "Local Farmer"
        farmer_upi = "9492147313@ybl" # Admin fallback
        if farmer_id:
            farmer = BaseModel.execute_query(
                "SELECT first_name, last_name, phone, upi_id FROM farmers WHERE id = %s",
                (int(farmer_id),), fetch_one=True
            )
            if farmer:
                farmer_name = f"{farmer['first_name']} {farmer['last_name']}".strip()
                # Auto check background verify / farmers number auto engine
                if farmer.get('upi_id'):
                    farmer_upi = farmer['upi_id']
                elif farmer.get('phone'):
                    farmer_upi = f"{farmer['phone']}@ybl"

        tax_amt = float(total_amount) - float(subtotal)
        if tax_amt < 0:
            tax_amt = 0.0

        result = {
            'success': True,
            'order_id': oid,
            'order_number': order_number,
            'total_amount': total_amount,
            'payment_method': payment_method,
            'payment_status': payment_status,
            'order_status': order_status,
            'farmer_share': float(subtotal),
            'admin_share': float(tax_amt) + float(delivery_fee),
            'farmer_name': farmer_name,
            'farmer_upi': farmer_upi,
            'admin_upi': '9492147313@ybl',
        }
        
        # For COD — order is immediately confirmed
        if payment_method == 'cod':
            result['message'] = 'Order confirmed! Pay on delivery.'
        else:
            result['message'] = 'Order created. Complete payment to confirm.'
        
        return JSONResponse(content=result)
    
    except Exception as e:
        print(f"Create order error: {e}")
        import traceback; traceback.print_exc()
        return JSONResponse(status_code=500, content={'error': str(e)})


# ============================================================================
# 3. RAZORPAY ORDER — For online payments
# ============================================================================

@checkout_router.post('/razorpay-order')
async def create_razorpay_order(request: Request, user_id: str = Depends(get_current_user)):
    """Create Razorpay order for online payment"""
    try:
        data = await request.json()
        order_id = data.get('order_id')
        
        if not order_id:
            return JSONResponse(status_code=400, content={'error': 'Order ID required'})
        
        order = BaseModel.execute_query(
            "SELECT * FROM checkout_orders WHERE id = %s AND buyer_id = %s",
            (order_id, int(user_id)), fetch_one=True
        )
        
        if not order:
            return JSONResponse(status_code=404, content={'error': 'Order not found'})
        
        if not razorpay_client:
            return JSONResponse(status_code=503, content={'error': 'Payment gateway not configured'})
        
        amount_paise = int(float(order['total_amount']) * 100)
        
        rz_order = razorpay_client.order.create({
            'amount': amount_paise,
            'currency': 'INR',
            'receipt': order['order_number'],
            'notes': {
                'order_id': str(order_id),
                'buyer_id': str(user_id),
            }
        })
        
        # Store razorpay order ID
        BaseModel.execute_query(
            "UPDATE checkout_orders SET razorpay_order_id = %s WHERE id = %s",
            (rz_order['id'], order_id)
        )
        
        return JSONResponse(content={
            'success': True,
            'razorpay_order_id': rz_order['id'],
            'razorpay_key_id': RAZORPAY_KEY_ID,
            'amount': amount_paise,
            'currency': 'INR',
            'order_number': order['order_number'],
            'buyer_name': order.get('buyer_name', ''),
            'buyer_email': order.get('buyer_email', ''),
            'buyer_phone': order.get('buyer_phone', ''),
        })
    
    except Exception as e:
        print(f"Razorpay order error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})


# ============================================================================
# 4. VERIFY PAYMENT — After Razorpay callback
# ============================================================================

@checkout_router.post('/verify-payment')
async def verify_payment(request: Request, user_id: str = Depends(get_current_user)):
    """Verify Razorpay payment signature and confirm order"""
    try:
        data = await request.json()
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_signature = data.get('razorpay_signature')
        order_id = data.get('order_id')
        
        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            return JSONResponse(status_code=400, content={'error': 'Missing payment data'})
        
        # Verify signature
        if RAZORPAY_KEY_SECRET:
            message = f"{razorpay_order_id}|{razorpay_payment_id}"
            expected_signature = hmac.new(
                RAZORPAY_KEY_SECRET.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            if expected_signature != razorpay_signature:
                # Update payment status to failed
                if order_id:
                    BaseModel.execute_query(
                        "UPDATE checkout_orders SET payment_status = 'FAILED' WHERE id = %s",
                        (order_id,)
                    )
                    _add_status_history(order_id, 'PAYMENT_FAILED', 'Signature verification failed', 'system')
                return JSONResponse(status_code=400, content={'error': 'Payment verification failed'})
        
        # Find order
        order = BaseModel.execute_query(
            "SELECT * FROM checkout_orders WHERE razorpay_order_id = %s",
            (razorpay_order_id,), fetch_one=True
        )
        
        if not order:
            return JSONResponse(status_code=404, content={'error': 'Order not found'})
        
        oid = order['id']
        
        # Update order: PAID + CONFIRMED
        BaseModel.execute_query(
            """UPDATE checkout_orders 
               SET payment_status = 'PAID', 
                   order_status = 'CONFIRMED',
                   razorpay_payment_id = %s, 
                   razorpay_signature = %s,
                   updated_at = NOW()
               WHERE id = %s""",
            (razorpay_payment_id, razorpay_signature, oid)
        )
        
        # Record payment transaction
        txn_id = _generate_txn_id()
        BaseModel.execute_query(
            """INSERT INTO checkout_payments 
               (order_id, transaction_id, payment_method, amount, status,
                razorpay_order_id, razorpay_payment_id, razorpay_signature)
               VALUES (%s, %s, 'online', %s, 'SUCCESS', %s, %s, %s)""",
            (oid, txn_id, float(order['total_amount']),
             razorpay_order_id, razorpay_payment_id, razorpay_signature)
        )
        
        _add_status_history(oid, 'CONFIRMED', f'Payment verified: {razorpay_payment_id}', 'system')
        
        return JSONResponse(content={
            'success': True,
            'message': 'Payment verified! Order confirmed.',
            'order_id': oid,
            'order_number': order['order_number'],
            'payment_status': 'PAID',
            'order_status': 'CONFIRMED',
            'transaction_id': txn_id,
        })
    
    except Exception as e:
        print(f"Verify payment error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})


@checkout_router.post('/verify-upi')
async def verify_upi_payment(request: Request, user_id: str = Depends(get_current_user)):
    """Verify manual UPI QR payment using UTR/Transaction ID, and confirm order"""
    try:
        data = await request.json()
        order_id = data.get('order_id')
        utr_number = data.get('transaction_id', '').strip()
        upi_id = data.get('upi_id', '9492147313@ybl').strip()
        
        if not order_id or not utr_number:
            return JSONResponse(status_code=400, content={'error': 'Order ID and Transaction ID (UTR) are required'})
            
        if len(utr_number) != 12 or not utr_number.isdigit():
            return JSONResponse(status_code=400, content={'error': 'UTR / Transaction ID must be a 12-digit number'})

        # Check if transaction ID has been used before (background verify engine check)
        txn_id = f"UPI-{utr_number}"
        existing = BaseModel.execute_query(
            "SELECT id FROM checkout_payments WHERE transaction_id = %s",
            (txn_id,), fetch_one=True
        ) or BaseModel.execute_query(
            "SELECT id FROM payments WHERE transaction_id = %s",
            (txn_id,), fetch_one=True
        )
        if existing:
            return JSONResponse(status_code=400, content={'error': 'This transaction ID (UTR) has already been verified for another order'})

        # Find the order
        order = BaseModel.execute_query(
            "SELECT * FROM checkout_orders WHERE id = %s AND buyer_id = %s",
            (order_id, int(user_id)), fetch_one=True
        )
        
        if not order:
            return JSONResponse(status_code=404, content={'error': 'Order not found'})
            
        # Update checkout order status to PAID + CONFIRMED
        BaseModel.execute_query(
            """UPDATE checkout_orders 
               SET payment_status = 'PAID', 
                   order_status = 'CONFIRMED',
                   razorpay_payment_id = %s,
                   razorpay_order_id = %s,
                   updated_at = NOW()
               WHERE id = %s""",
            (utr_number, upi_id, order_id)
        )
        
        # Record checkout payment
        txn_id = f"UPI-{utr_number}"
        BaseModel.execute_query(
            """INSERT INTO checkout_payments 
               (order_id, transaction_id, payment_method, amount, status)
               VALUES (%s, %s, 'online', %s, 'SUCCESS')""",
            (order_id, txn_id, float(order['total_amount']))
        )
        
        # ALSO write to the main `payments` table for central Admin Receipts & Analytics!
        BaseModel.execute_query(
            """INSERT INTO payments 
               (order_id, buyer_id, amount, payment_method, status, transaction_id)
               VALUES (%s, %s, %s, 'online', 'completed', %s)
               ON CONFLICT DO NOTHING""",
            (order_id, int(user_id), float(order['total_amount']), txn_id)
        )
        
        # Send notifications
        from models.models import Notification
        try:
            Notification.create(
                user_id=str(user_id),
                title='Payment Received',
                message=f"Payment for order #{order['order_number']} verified successfully",
                notification_type='payment'
            )
            Notification.create(
                user_id=str(order['farmer_id']),
                title='Order Confirmed',
                message=f"Order #{order['order_number']} has been paid and confirmed",
                notification_type='order'
            )
        except Exception:
            pass

        _add_status_history(order_id, 'CONFIRMED', f'UPI payment verified. UTR: {utr_number}', 'system')
        
        return JSONResponse(content={
            'success': True,
            'message': 'Payment verified! Order confirmed.',
            'order_id': order_id,
            'order_number': order['order_number'],
            'payment_status': 'PAID',
            'order_status': 'CONFIRMED',
            'transaction_id': txn_id,
        })
    except Exception as e:
        print(f"Verify UPI payment error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})


# ============================================================================
# 5. BUYER — GET ORDERS
# ============================================================================

@checkout_router.get('/orders')
async def get_buyer_orders(request: Request, user_id: str = Depends(get_current_user)):
    """Get buyer's orders"""
    try:
        orders = BaseModel.execute_query(
            """SELECT co.*, 
                      CONCAT(f.first_name, ' ', f.last_name) as farmer_name,
                      f.phone as farmer_phone, f.location as farmer_location
               FROM checkout_orders co
               LEFT JOIN farmers f ON co.farmer_id = f.id
               WHERE co.buyer_id = %s
               ORDER BY co.created_at DESC""",
            (int(user_id),), fetch_all=True
        ) or []
        
        if not orders:
            return JSONResponse(content={'success': True, 'orders': []})
            
        order_ids = [order['id'] for order in orders]
        placeholders = ', '.join(['%s'] * len(order_ids))
        all_items = BaseModel.execute_query(
            f"SELECT * FROM checkout_order_items WHERE order_id IN ({placeholders})",
            tuple(order_ids), fetch_all=True
        ) or []
        
        items_by_order = {}
        for item in all_items:
            oid = item['order_id']
            if oid not in items_by_order:
                items_by_order[oid] = []
            items_by_order[oid].append(_serialize_dt(item))
            
        result = []
        for order in orders:
            o = _serialize_dt(order)
            o['items'] = items_by_order.get(order['id'], [])
            result.append(o)
        
        return JSONResponse(content={'success': True, 'orders': result})
    except Exception as e:
        print(f"Get orders error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})


# ============================================================================
# 6. BUYER — GET ORDER DETAIL + TRACKING
# ============================================================================

@checkout_router.get('/orders/{order_id}')
async def get_order_detail(order_id: int, request: Request, user_id: str = Depends(get_current_user)):
    """Get order detail with tracking timeline"""
    try:
        order = BaseModel.execute_query(
            """SELECT co.*,
                      CONCAT(f.first_name, ' ', f.last_name) as farmer_name,
                      f.phone as farmer_phone, f.location as farmer_location,
                      f.latitude as farmer_lat, f.longitude as farmer_lng
               FROM checkout_orders co
               LEFT JOIN farmers f ON co.farmer_id = f.id
               WHERE co.id = %s AND co.buyer_id = %s""",
            (order_id, int(user_id)), fetch_one=True
        )
        
        if not order:
            return JSONResponse(status_code=404, content={'error': 'Order not found'})
        
        items = BaseModel.execute_query(
            "SELECT * FROM checkout_order_items WHERE order_id = %s",
            (order_id,), fetch_all=True
        ) or []
        
        tracking = BaseModel.execute_query(
            "SELECT * FROM order_status_history WHERE order_id = %s ORDER BY created_at ASC",
            (order_id,), fetch_all=True
        ) or []
        
        payment = BaseModel.execute_query(
            "SELECT * FROM checkout_payments WHERE order_id = %s ORDER BY created_at DESC LIMIT 1",
            (order_id,), fetch_one=True
        )
        
        result = _serialize_dt(order)
        result['items'] = [_serialize_dt(i) for i in items]
        result['tracking'] = [_serialize_dt(t) for t in tracking]
        result['payment'] = _serialize_dt(payment) if payment else None
        
        return JSONResponse(content={'success': True, 'order': result})
    except Exception as e:
        print(f"Order detail error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})


# ============================================================================
# 7. BUYER — CANCEL ORDER
# ============================================================================

@checkout_router.post('/orders/{order_id}/cancel')
async def cancel_order(order_id: int, request: Request, user_id: str = Depends(get_current_user)):
    """Cancel order (only before PACKED status)"""
    try:
        data = await request.json()
        reason = data.get('reason', 'Cancelled by buyer')
        
        order = BaseModel.execute_query(
            "SELECT * FROM checkout_orders WHERE id = %s AND buyer_id = %s",
            (order_id, int(user_id)), fetch_one=True
        )
        
        if not order:
            return JSONResponse(status_code=404, content={'error': 'Order not found'})
        
        non_cancellable = ['PACKED', 'OUT_FOR_DELIVERY', 'DELIVERED', 'CANCELLED']
        if order['order_status'] in non_cancellable:
            return JSONResponse(status_code=400, content={
                'error': f"Cannot cancel order in {order['order_status']} status"
            })
        
        BaseModel.execute_query(
            """UPDATE checkout_orders 
               SET order_status = 'CANCELLED', cancelled_at = NOW(), cancel_reason = %s, updated_at = NOW()
               WHERE id = %s""",
            (reason, order_id)
        )
        
        # If payment was made, mark for refund
        if order['payment_status'] == 'PAID':
            BaseModel.execute_query(
                "UPDATE checkout_orders SET payment_status = 'REFUNDED' WHERE id = %s",
                (order_id,)
            )
        
        _add_status_history(order_id, 'CANCELLED', reason, 'buyer')
        
        return JSONResponse(content={'success': True, 'message': 'Order cancelled'})
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})


# ============================================================================
# 8. FARMER — GET INCOMING ORDERS
# ============================================================================

@checkout_router.get('/farmer-orders')
async def get_farmer_orders(request: Request, user_id: str = Depends(get_current_user)):
    """Get farmer's incoming orders"""
    try:
        orders = BaseModel.execute_query(
            """SELECT co.*,
                      CONCAT(b.first_name, ' ', b.last_name) as buyer_display_name,
                      b.phone as buyer_display_phone, b.email as buyer_display_email
               FROM checkout_orders co
               LEFT JOIN buyers b ON co.buyer_id = b.id
               WHERE co.farmer_id = %s
               ORDER BY co.created_at DESC""",
            (int(user_id),), fetch_all=True
        ) or []
        
        if not orders:
            return JSONResponse(content={'success': True, 'orders': []})
            
        order_ids = [order['id'] for order in orders]
        placeholders = ', '.join(['%s'] * len(order_ids))
        all_items = BaseModel.execute_query(
            f"SELECT * FROM checkout_order_items WHERE order_id IN ({placeholders})",
            tuple(order_ids), fetch_all=True
        ) or []
        
        items_by_order = {}
        for item in all_items:
            oid = item['order_id']
            if oid not in items_by_order:
                items_by_order[oid] = []
            items_by_order[oid].append(_serialize_dt(item))
            
        result = []
        for order in orders:
            o = _serialize_dt(order)
            o['items'] = items_by_order.get(order['id'], [])
            result.append(o)
        
        return JSONResponse(content={'success': True, 'orders': result})
    except Exception as e:
        print(f"Farmer orders error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})


# ============================================================================
# 9. FARMER — ACCEPT ORDER
# ============================================================================

@checkout_router.post('/farmer-orders/{order_id}/accept')
async def accept_order(order_id: int, request: Request, user_id: str = Depends(get_current_user)):
    """Farmer accepts incoming order"""
    try:
        order = BaseModel.execute_query(
            "SELECT * FROM checkout_orders WHERE id = %s AND farmer_id = %s",
            (order_id, int(user_id)), fetch_one=True
        )
        
        if not order:
            return JSONResponse(status_code=404, content={'error': 'Order not found'})
        
        if order['order_status'] not in ['CONFIRMED', 'PLACED']:
            return JSONResponse(status_code=400, content={
                'error': f"Cannot accept order in {order['order_status']} status"
            })
        
        BaseModel.execute_query(
            "UPDATE checkout_orders SET order_status = 'ACCEPTED', updated_at = NOW() WHERE id = %s",
            (order_id,)
        )
        _add_status_history(order_id, 'ACCEPTED', 'Order accepted by farmer', 'farmer')
        
        return JSONResponse(content={'success': True, 'message': 'Order accepted!'})
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})


# ============================================================================
# 10. FARMER — REJECT ORDER
# ============================================================================

@checkout_router.post('/farmer-orders/{order_id}/reject')
async def reject_order(order_id: int, request: Request, user_id: str = Depends(get_current_user)):
    """Farmer rejects order"""
    try:
        data = await request.json()
        reason = data.get('reason', 'Rejected by farmer')
        
        order = BaseModel.execute_query(
            "SELECT * FROM checkout_orders WHERE id = %s AND farmer_id = %s",
            (order_id, int(user_id)), fetch_one=True
        )
        
        if not order:
            return JSONResponse(status_code=404, content={'error': 'Order not found'})
        
        BaseModel.execute_query(
            """UPDATE checkout_orders 
               SET order_status = 'CANCELLED', cancel_reason = %s, cancelled_at = NOW(), updated_at = NOW()
               WHERE id = %s""",
            (reason, order_id)
        )
        
        if order['payment_status'] == 'PAID':
            BaseModel.execute_query(
                "UPDATE checkout_orders SET payment_status = 'REFUNDED' WHERE id = %s",
                (order_id,)
            )
        
        _add_status_history(order_id, 'REJECTED', reason, 'farmer')
        
        return JSONResponse(content={'success': True, 'message': 'Order rejected'})
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})


# ============================================================================
# 11. FARMER — UPDATE ORDER STATUS
# ============================================================================

@checkout_router.post('/farmer-orders/{order_id}/status')
async def update_order_status(order_id: int, request: Request, user_id: str = Depends(get_current_user)):
    """Farmer updates order status through delivery flow"""
    try:
        data = await request.json()
        new_status = data.get('status', '').upper()
        
        valid_statuses = ['ACCEPTED', 'PACKED', 'OUT_FOR_DELIVERY', 'DELIVERED']
        if new_status not in valid_statuses:
            return JSONResponse(status_code=400, content={'error': f'Invalid status: {new_status}'})
        
        order = BaseModel.execute_query(
            "SELECT * FROM checkout_orders WHERE id = %s AND farmer_id = %s",
            (order_id, int(user_id)), fetch_one=True
        )
        
        if not order:
            return JSONResponse(status_code=404, content={'error': 'Order not found'})
        
        update_fields = "order_status = %s, updated_at = NOW()"
        params = [new_status]
        
        if new_status == 'DELIVERED':
            update_fields += ", delivered_at = NOW()"
            # For online payments, credit farmer wallet on delivery
            if order['payment_status'] == 'PAID':
                _credit_farmer_wallet(
                    order['farmer_id'], order_id,
                    order['subtotal'], order['platform_fee']
                )
        
        params.append(order_id)
        BaseModel.execute_query(
            f"UPDATE checkout_orders SET {update_fields} WHERE id = %s",
            tuple(params)
        )
        
        status_descriptions = {
            'ACCEPTED': 'Order accepted by farmer',
            'PACKED': 'Order packed and ready',
            'OUT_FOR_DELIVERY': 'Order is out for delivery',
            'DELIVERED': 'Order delivered successfully',
        }
        _add_status_history(order_id, new_status, status_descriptions.get(new_status, ''), 'farmer')
        
        return JSONResponse(content={
            'success': True,
            'message': f'Order status updated to {new_status}',
            'order_status': new_status
        })
    except Exception as e:
        print(f"Update status error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})


# ============================================================================
# 12. FARMER — COLLECT CASH (COD)
# ============================================================================

@checkout_router.post('/farmer-orders/{order_id}/collect-cash')
async def collect_cash(order_id: int, request: Request, user_id: str = Depends(get_current_user)):
    """Mark COD payment as collected"""
    try:
        order = BaseModel.execute_query(
            "SELECT * FROM checkout_orders WHERE id = %s AND farmer_id = %s",
            (order_id, int(user_id)), fetch_one=True
        )
        
        if not order:
            return JSONResponse(status_code=404, content={'error': 'Order not found'})
        
        if order['payment_method'] != 'cod':
            return JSONResponse(status_code=400, content={'error': 'Not a COD order'})
        
        BaseModel.execute_query(
            """UPDATE checkout_orders 
               SET payment_status = 'CASH_COLLECTED', updated_at = NOW()
               WHERE id = %s""",
            (order_id,)
        )
        
        # ALSO write to the main `payments` table for central Admin Receipts & Analytics!
        txn_id = f"COD-{order_id}"
        BaseModel.execute_query(
            """INSERT INTO payments 
               (order_id, buyer_id, amount, payment_method, status, transaction_id)
               VALUES (%s, %s, %s, 'cash', 'completed', %s)
               ON CONFLICT DO NOTHING""",
            (order_id, order['buyer_id'], float(order['total_amount']), txn_id)
        )
        
        # Credit farmer wallet (minus platform fee)
        _credit_farmer_wallet(
            order['farmer_id'], order_id,
            order['subtotal'], order['platform_fee']
        )
        
        _add_status_history(order_id, 'CASH_COLLECTED', 'Cash collected from buyer', 'farmer')
        
        return JSONResponse(content={'success': True, 'message': 'Cash collected!'})
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})


# ============================================================================
# 13. FARMER WALLET
# ============================================================================

@checkout_router.get('/wallet')
async def get_wallet(request: Request, user_id: str = Depends(get_current_user)):
    """Get farmer wallet balance"""
    try:
        wallet = BaseModel.execute_query(
            "SELECT * FROM farmer_wallets WHERE farmer_id = %s",
            (int(user_id),), fetch_one=True
        )
        
        if not wallet:
            wallet = {
                'available_balance': 0,
                'total_earnings': 0,
                'total_commission': 0,
                'pending_settlement': 0,
            }
        
        # Count orders
        order_stats = BaseModel.execute_query(
            """SELECT 
                COUNT(*) as total_orders,
                COUNT(CASE WHEN order_status = 'DELIVERED' THEN 1 END) as delivered,
                COUNT(CASE WHEN order_status IN ('CONFIRMED','ACCEPTED','PACKED','OUT_FOR_DELIVERY') THEN 1 END) as active,
                COUNT(CASE WHEN payment_status = 'PENDING' AND payment_method = 'cod' THEN 1 END) as pending_cod
               FROM checkout_orders WHERE farmer_id = %s""",
            (int(user_id),), fetch_one=True
        ) or {}
        
        return JSONResponse(content={
            'success': True,
            'wallet': _serialize_dt(wallet) if isinstance(wallet, dict) and 'created_at' in wallet else wallet,
            'stats': order_stats
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})


@checkout_router.get('/wallet/transactions')
async def get_wallet_transactions(request: Request, user_id: str = Depends(get_current_user)):
    """Get wallet transaction history"""
    try:
        transactions = BaseModel.execute_query(
            """SELECT wt.*, co.order_number 
               FROM wallet_transactions wt
               LEFT JOIN checkout_orders co ON wt.order_id = co.id
               WHERE wt.farmer_id = %s
               ORDER BY wt.created_at DESC
               LIMIT 50""",
            (int(user_id),), fetch_all=True
        ) or []
        
        return JSONResponse(content={
            'success': True,
            'transactions': [_serialize_dt(t) for t in transactions]
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})


# ============================================================================
# 14. DELIVERY ADDRESSES
# ============================================================================

@checkout_router.get('/addresses')
async def get_addresses(request: Request, user_id: str = Depends(get_current_user)):
    """Get buyer's saved addresses"""
    try:
        addresses = BaseModel.execute_query(
            "SELECT * FROM delivery_addresses WHERE buyer_id = %s ORDER BY is_default DESC, created_at DESC",
            (int(user_id),), fetch_all=True
        ) or []
        
        return JSONResponse(content={
            'success': True,
            'addresses': [_serialize_dt(a) for a in addresses]
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})


@checkout_router.post('/addresses')
async def save_address(request: Request, user_id: str = Depends(get_current_user)):
    """Save delivery address"""
    try:
        data = await request.json()
        
        addr_id = BaseModel.execute_query(
            """INSERT INTO delivery_addresses 
               (buyer_id, label, full_name, phone, address_line1, address_line2, city, state, pincode, landmark, is_default)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               RETURNING id""",
            (int(user_id), data.get('label', 'Home'), data.get('full_name', ''),
             data.get('phone', ''), data.get('address_line1', ''), data.get('address_line2', ''),
             data.get('city', ''), data.get('state', ''), data.get('pincode', ''),
             data.get('landmark', ''), data.get('is_default', False)),
            fetch_one=True
        )
        
        return JSONResponse(content={'success': True, 'address_id': addr_id['id'] if addr_id else None})
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})


# ============================================================================
# 15. ADMIN — PAYMENT DASHBOARD
# ============================================================================

@checkout_router.get('/admin/dashboard')
async def admin_payment_dashboard(request: Request, user_id: str = Depends(get_current_user)):
    """Admin payment & order statistics"""
    try:
        stats = BaseModel.execute_query(
            """SELECT 
                COUNT(*) as total_orders,
                COALESCE(SUM(total_amount), 0) as total_revenue,
                COUNT(CASE WHEN payment_status = 'PAID' THEN 1 END) as paid_orders,
                COUNT(CASE WHEN payment_status = 'PENDING' THEN 1 END) as pending_payments,
                COUNT(CASE WHEN payment_status = 'FAILED' THEN 1 END) as failed_payments,
                COUNT(CASE WHEN payment_status = 'CASH_COLLECTED' THEN 1 END) as cod_collected,
                COUNT(CASE WHEN payment_method = 'cod' THEN 1 END) as cod_orders,
                COUNT(CASE WHEN payment_method = 'online' THEN 1 END) as online_orders,
                COALESCE(SUM(platform_fee), 0) as total_platform_fees,
                COALESCE(SUM(delivery_fee), 0) as total_delivery_fees,
                COUNT(CASE WHEN order_status = 'DELIVERED' THEN 1 END) as delivered_orders,
                COUNT(CASE WHEN order_status = 'CANCELLED' THEN 1 END) as cancelled_orders
               FROM checkout_orders""",
            fetch_one=True
        ) or {}
        
        # Recent orders
        recent = BaseModel.execute_query(
            """SELECT co.id, co.order_number, co.total_amount, co.payment_method, 
                      co.payment_status, co.order_status, co.created_at,
                      co.buyer_name
               FROM checkout_orders co
               ORDER BY co.created_at DESC LIMIT 20""",
            fetch_all=True
        ) or []
        
        return JSONResponse(content={
            'success': True,
            'stats': _serialize_dt(stats),
            'recent_orders': [_serialize_dt(r) for r in recent]
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})


# ============================================================================
# STRIPE CHECKOUT — Card payments via Stripe Checkout Sessions
# ============================================================================

@checkout_router.post('/create-stripe-session')
async def create_stripe_session(request: Request, user_id: str = Depends(get_current_user)):
    """Create a Stripe Checkout Session for an existing order"""
    if not stripe_client:
        return JSONResponse(status_code=503, content={
            'success': False, 'error': 'Stripe is not configured. Please use another payment method.'
        })

    data = await request.json()
    order_id = data.get('order_id')

    if not order_id:
        return JSONResponse(status_code=400, content={'success': False, 'error': 'order_id is required'})

    # Fetch order
    order = BaseModel.execute_query(
        "SELECT * FROM checkout_orders WHERE id = %s AND buyer_id = %s",
        (order_id, user_id), fetch_one=True
    )
    if not order:
        return JSONResponse(status_code=404, content={'success': False, 'error': 'Order not found'})

    if order.get('payment_status') == 'PAID':
        return JSONResponse(status_code=400, content={'success': False, 'error': 'Order is already paid'})

    amount_inr = float(order['total_amount'])
    amount_paise = int(amount_inr * 100)  # Stripe uses smallest currency unit

    try:
        session = stripe_client.checkout.Session.create(
            payment_method_types=['card'],
            mode='payment',
            currency='inr',
            line_items=[{
                'price_data': {
                    'currency': 'inr',
                    'unit_amount': amount_paise,
                    'product_data': {
                        'name': f'SmartFarm Order #{order.get("order_number", order_id)}',
                        'description': f'Order from SmartFarm Marketplace',
                    },
                },
                'quantity': 1,
            }],
            metadata={
                'order_id': str(order_id),
                'buyer_id': str(user_id),
                'order_number': order.get('order_number', ''),
            },
            customer_email=order.get('buyer_email', ''),
            success_url=f'{FRONTEND_URL}/buyer/order-success?session_id={{CHECKOUT_SESSION_ID}}&order_id={order_id}',
            cancel_url=f'{FRONTEND_URL}/buyer/checkout?cancelled=true',
            expires_after=1800,  # 30 min expiry
        )

        # Store session ID on order
        BaseModel.execute_query(
            "UPDATE checkout_orders SET payment_method = 'stripe', razorpay_order_id = %s WHERE id = %s",
            (session.id, order_id)
        )

        return {
            'success': True,
            'session_id': session.id,
            'session_url': session.url,
            'stripe_publishable_key': STRIPE_PUBLISHABLE_KEY,
        }

    except Exception as e:
        print(f"[Stripe] Session creation error: {e}")
        return JSONResponse(status_code=500, content={'success': False, 'error': 'Failed to create payment session'})


@checkout_router.post('/verify-stripe')
async def verify_stripe_payment(request: Request, user_id: str = Depends(get_current_user)):
    """Verify Stripe payment after redirect — called from frontend success page"""
    if not stripe_client:
        return JSONResponse(status_code=503, content={'success': False, 'error': 'Stripe not configured'})

    data = await request.json()
    session_id = data.get('session_id')
    order_id = data.get('order_id')

    if not session_id:
        return JSONResponse(status_code=400, content={'success': False, 'error': 'session_id is required'})

    try:
        session = stripe_client.checkout.Session.retrieve(session_id)

        if session.payment_status != 'paid':
            return JSONResponse(content={'success': False, 'error': 'Payment not completed', 'status': session.payment_status})

        # Mark order as paid
        oid = order_id or session.metadata.get('order_id')
        if oid:
            BaseModel.execute_query(
                """UPDATE checkout_orders 
                   SET payment_status = 'PAID', 
                       order_status = 'CONFIRMED',
                       razorpay_payment_id = %s
                   WHERE id = %s AND buyer_id = %s""",
                (session.payment_intent, oid, user_id)
            )

        return {
            'success': True,
            'payment_status': 'PAID',
            'transaction_id': session.payment_intent,
            'order_id': oid,
        }

    except Exception as e:
        print(f"[Stripe] Verify error: {e}")
        return JSONResponse(status_code=500, content={'success': False, 'error': 'Payment verification failed'})


@checkout_router.post('/stripe-webhook')
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events (payment confirmation, refunds, etc.)"""
    if not stripe_client:
        return JSONResponse(status_code=503, content={'error': 'Stripe not configured'})

    payload = await request.body()
    sig_header = request.headers.get('stripe-signature', '')

    try:
        if STRIPE_WEBHOOK_SECRET:
            event = stripe_client.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
        else:
            event = json.loads(payload)
    except Exception as e:
        print(f"[Stripe Webhook] Signature verification failed: {e}")
        return JSONResponse(status_code=400, content={'error': 'Invalid signature'})

    event_type = event.get('type', '')

    if event_type == 'checkout.session.completed':
        session = event['data']['object']
        order_id = session.get('metadata', {}).get('order_id')
        if order_id and session.get('payment_status') == 'paid':
            BaseModel.execute_query(
                """UPDATE checkout_orders 
                   SET payment_status = 'PAID', 
                       order_status = 'CONFIRMED',
                       razorpay_payment_id = %s
                   WHERE id = %s""",
                (session.get('payment_intent'), order_id)
            )
            print(f"[Stripe Webhook] Order {order_id} marked as PAID")

    elif event_type == 'payment_intent.payment_failed':
        intent = event['data']['object']
        print(f"[Stripe Webhook] Payment failed: {intent.get('id')}")

    return {'received': True}
