"""
Payment & Receipt Routes
Handles: Razorpay orders, payment verification, direct sales,
         receipts, PDF generation, receipt delivery, transaction history
"""

from fastapi import APIRouter, Request, Query, Depends
from fastapi.responses import JSONResponse
from utils.jwt_utils import get_current_user
from utils.email_service import EmailService
from models.models import BaseModel
from datetime import datetime
from dotenv import load_dotenv
import os
import json
import random

load_dotenv()

# ---------------------------------------------------------------------------
# Optional: Razorpay
# ---------------------------------------------------------------------------
razorpay_client = None
try:
    import razorpay
    rz_key = os.getenv('RAZORPAY_KEY_ID')
    rz_secret = os.getenv('RAZORPAY_KEY_SECRET')
    if rz_key and rz_secret:
        razorpay_client = razorpay.Client(auth=(rz_key, rz_secret))
        print("[OK] Razorpay client configured")
    else:
        print("[SKIP] Razorpay credentials not set")
except ImportError:
    print("[SKIP] razorpay not installed")

# ---------------------------------------------------------------------------
# Optional: Twilio
# ---------------------------------------------------------------------------
twilio_client = None
TWILIO_PHONE = None
TWILIO_WHATSAPP = None
try:
    from twilio.rest import Client as TwilioClient
    tw_sid = os.getenv('TWILIO_ACCOUNT_SID')
    tw_token = os.getenv('TWILIO_AUTH_TOKEN')
    if tw_sid and tw_token:
        twilio_client = TwilioClient(tw_sid, tw_token)
        TWILIO_PHONE = os.getenv('TWILIO_PHONE_NUMBER')
        TWILIO_WHATSAPP = os.getenv('TWILIO_WHATSAPP_NUMBER', TWILIO_PHONE)
        print("[OK] Twilio (payments) configured")
    else:
        print("[SKIP] Twilio credentials not set (payments)")
except ImportError:
    print("[SKIP] twilio not installed (payments)")

# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------
payments_router = APIRouter(prefix='/api/payments', tags=['Payments'])

# ============================================================================
# HELPERS
# ============================================================================

async def _generate_receipt_id():
    """Generate unique receipt ID: SF-YYYY-NNNN"""
    year = datetime.now().strftime('%Y')
    # Get current max sequential number for this year
    query = """
        SELECT receipt_id FROM receipts
        WHERE receipt_id LIKE %s
        ORDER BY id DESC LIMIT 1
    """
    last = BaseModel.execute_query(query, (f'SF-{year}-%',), fetch_one=True)
    if last and last.get('receipt_id'):
        try:
            seq = int(last['receipt_id'].split('-')[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1
    return f"SF-{year}-{seq:04d}"


async def _generate_transaction_id():
    """Generate unique transaction ID: TXN-timestamp-random4"""
    ts = datetime.now().strftime('%Y%m%d%H%M%S')
    rand = random.randint(1000, 9999)
    return f"TXN-{ts}-{rand}"


async def _serialize_row(row):
    """Convert datetime objects in a dict so it is JSON-serializable."""
    if row is None:
        return None
    out = {}
    for k, v in row.items():
        if isinstance(v, datetime):
            out[k] = v.isoformat()
        else:
            out[k] = v
    return out


async def _send_email(to_email, subject, body_html):
    """Send email via SMTP (centralized EmailService)."""
    return EmailService._send_email(to_email, subject, body_html)


# ============================================================================
# PAYMENT OTP — Generate & Verify
# ============================================================================

@payments_router.post('/generate-payment-otp')
async def generate_payment_otp(request: Request, user_id: str = Depends(get_current_user)):
    """Generate OTP for buyer payment confirmation, send via email."""
    try:
        buyer_id = user_id
        data = await request.json()
        amount = float(data.get('amount', 0))
        product_details = json.dumps(data.get('items', []))
        farmer_id = data.get('farmer_id')
        buyer_email = data.get('buyer_email', '')
        buyer_phone = data.get('buyer_phone', '')

        if amount <= 0:
            return JSONResponse(status_code=400, content={'error': 'Invalid amount'})

        # Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))
        expires_at = datetime.now() + __import__('datetime').timedelta(minutes=10)

        # Store OTP (PostgreSQL uses RETURNING id via execute_insert)
        otp_ref = BaseModel.execute_insert(
            """INSERT INTO payment_otps (buyer_id, buyer_phone, buyer_email, otp, amount, product_details, farmer_id, status, expires_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending', %s)""",
            (int(buyer_id), buyer_phone, buyer_email, otp, amount, product_details, farmer_id, expires_at)
        )

        # Send OTP via email
        if buyer_email:
            otp_html = f"""
            <div style="font-family:Arial,sans-serif;max-width:420px;margin:auto;padding:24px;background:#f0fdf4;border-radius:16px;text-align:center;">
                <h2 style="color:#166534;">🔐 Payment Verification OTP</h2>
                <p style="color:#555;">Your one-time password for payment of</p>
                <h1 style="color:#166534;font-size:32px;margin:8px 0;">₹{amount:.2f}</h1>
                <div style="background:#166534;color:#fff;font-size:36px;letter-spacing:12px;padding:16px 24px;border-radius:12px;display:inline-block;margin:16px 0;font-weight:700;">
                    {otp}
                </div>
                <p style="color:#888;font-size:13px;">This OTP expires in 10 minutes.<br/>Do not share this OTP with anyone.</p>
                <p style="color:#166534;font-weight:600;margin-top:16px;">SmartFarming Market Place</p>
            </div>
            """
            _send_email(buyer_email, f'Payment OTP: {otp} - SmartFarming', otp_html)

        return {
            'success': True,
            'otp_reference': otp_ref,
            'message': 'OTP sent to your email',
            'expires_in': 600,
        }

    except Exception as e:
        import traceback; traceback.print_exc()
        return JSONResponse(status_code=500, content={'error': str(e)})


@payments_router.post('/verify-payment-otp')
async def verify_payment_otp(request: Request):
    """Verify payment OTP — public endpoint (no JWT). Returns order details for success screen."""
    try:
        data = await request.json()
        otp = data.get('otp', '').strip()

        if not otp or len(otp) != 6:
            return JSONResponse(status_code=400, content={'error': 'Enter a valid 6-digit OTP'})

        # Find matching OTP
        otp_record = BaseModel.execute_query(
            """SELECT * FROM payment_otps
               WHERE otp = %s AND status = 'pending' AND expires_at > NOW()
               ORDER BY created_at DESC LIMIT 1""",
            (otp,), fetch_one=True
        )

        if not otp_record:
            return JSONResponse(status_code=400, content={'error': 'Invalid or expired OTP'})

        # Mark as verified
        BaseModel.execute_query(
            "UPDATE payment_otps SET status = 'verified', verified_at = NOW() WHERE id = %s",
            (otp_record['id'],)
        )

        # Get farmer details
        farmer_info = {}
        if otp_record.get('farmer_id'):
            farmer = BaseModel.execute_query(
                "SELECT first_name, last_name, phone, email, upi_id, bank_name FROM farmers WHERE id = %s",
                (int(otp_record['farmer_id']),), fetch_one=True
            )
            if farmer:
                farmer_info = {
                    'name': f"{farmer.get('first_name', '')} {farmer.get('last_name', '')}".strip(),
                    'phone': farmer.get('phone', ''),
                    'upi_id': farmer.get('upi_id', ''),
                    'bank_name': farmer.get('bank_name', ''),
                }

        # Get buyer details
        buyer_info = {}
        if otp_record.get('buyer_id'):
            buyer = BaseModel.execute_query(
                "SELECT first_name, last_name, phone FROM buyers WHERE id = %s",
                (int(otp_record['buyer_id']),), fetch_one=True
            )
            if buyer:
                buyer_info = {
                    'name': f"{buyer.get('first_name', '')} {buyer.get('last_name', '')}".strip(),
                    'phone': buyer.get('phone', ''),
                }

        # Parse product details
        items = []
        try:
            items = json.loads(otp_record.get('product_details', '[]'))
        except:
            pass

        amount = float(otp_record['amount']) if otp_record.get('amount') else 0

        return JSONResponse(content={
            'success': True,
            'verified': True,
            'payment': {
                'amount': amount,
                'status': 'completed',
                'transaction_id': f'TXN-{otp_record["id"]}-{random.randint(1000,9999)}',
                'buyer': buyer_info,
                'farmer': farmer_info,
                'items': items,
                'verified_at': datetime.now().isoformat(),
            }
        }), 200

    except Exception as e:
        import traceback; traceback.print_exc()
        return JSONResponse(status_code=500, content={'error': str(e)})


# ============================================================================
# 1. POST /create-order  –  Create Razorpay Order
# ============================================================================

@payments_router.post('/create-order')
async def create_order(request: Request):
    """Create a Razorpay payment order."""
    try:
        if razorpay_client is None:
            return JSONResponse(status_code=503, content={'error': 'Razorpay is not configured'})

        data = await request.json()
        amount = data.get('amount')
        if not amount:
            return JSONResponse(status_code=400, content={'error': 'Amount is required'})

        currency = data.get('currency', 'INR')
        receipt_id = data.get('receipt_id', _generate_receipt_id())
        raw_notes = data.get('notes', {})
        delivery_address = data.get('delivery_address', '')

        # Razorpay requires 'notes' to be a dict/object, NOT a string
        if isinstance(raw_notes, str):
            notes = {'delivery_notes': raw_notes, 'delivery_address': delivery_address}
        elif isinstance(raw_notes, dict):
            notes = raw_notes
            if delivery_address:
                notes['delivery_address'] = delivery_address
        else:
            notes = {}

        # Frontend sends amount in RUPEES. Razorpay needs PAISE (1 rupee = 100 paise)
        amount_paise = int(float(amount) * 100)

        order_data = {
            'amount': amount_paise,
            'currency': currency,
            'receipt': receipt_id,
            'notes': notes,
        }

        rz_order = razorpay_client.order.create(data=order_data)

        return JSONResponse(status_code=201, content={
            'success': True,
            'order_id': rz_order['id'],
            'amount': amount_paise,
            'currency': currency,
            'key_id': os.getenv('RAZORPAY_KEY_ID'),
        })

    except Exception as e:
        print(f"Create order error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})


# ============================================================================
# 2. POST /verify  –  Verify Razorpay Payment
# ============================================================================

@payments_router.post('/verify')
async def verify_payment(request: Request):
    """Verify Razorpay payment signature, create payment + receipt + transaction."""
    try:
        if razorpay_client is None:
            return JSONResponse(status_code=503, content={'error': 'Razorpay is not configured'})

        data = await request.json()
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_signature = data.get('razorpay_signature')
        order_items = data.get('order_items', [])
        buyer_id = data.get('buyer_id')
        farmer_id = data.get('farmer_id')

        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            return JSONResponse(status_code=400, content={'error': 'Razorpay order_id, payment_id and signature are required'})

        # --- Verify signature ---
        try:
            razorpay_client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature,
            })
        except Exception:
            return JSONResponse(status_code=400, content={'error': 'Payment signature verification failed'})

        # --- Calculate totals ---
        total_amount = sum(
            float(item.get('quantity', 0)) * float(item.get('price_per_kg', 0))
            for item in order_items
        )

        # --- Create payment record ---
        payment_id = BaseModel.execute_insert(
            """INSERT INTO payments
               (buyer_id, amount, payment_method, status,
                razorpay_payment_id, razorpay_order_id, razorpay_signature,
                transaction_id, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())""",
            (buyer_id, total_amount, 'razorpay', 'completed',
             razorpay_payment_id, razorpay_order_id, razorpay_signature,
             razorpay_payment_id)
        )

        # --- Create receipt ---
        receipt_id = _generate_receipt_id()
        qr_code = f"https://smartfarm.app/verify/{receipt_id}"

        db_receipt_id = BaseModel.execute_insert(
            """INSERT INTO receipts
               (receipt_id, payment_id, buyer_id, farmer_id,
                subtotal, grand_total, payment_type, payment_status, qr_code, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())""",
            (receipt_id, payment_id, buyer_id, farmer_id,
             total_amount, total_amount, 'razorpay', 'completed', qr_code)
        )

        # --- Create receipt items ---
        for item in order_items:
            item_total = float(item.get('quantity', 0)) * float(item.get('price_per_kg', 0))
            BaseModel.execute_insert(
                """INSERT INTO receipt_items
                   (receipt_id, product_id, product_name, quantity_kg, price_per_kg, product_quality, item_total)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (db_receipt_id, item.get('product_id'), item.get('product_name'),
                 float(item.get('quantity', 0)), float(item.get('price_per_kg', 0)),
                 item.get('quality', 'Standard'), item_total)
            )

        # --- Create transaction record ---
        txn_id = _generate_transaction_id()
        BaseModel.execute_insert(
            """INSERT INTO transactions
               (transaction_id, payment_id, receipt_id, user_id, user_type,
                type, amount, description, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())""",
            (txn_id, payment_id, db_receipt_id, buyer_id, 'buyer',
             'debit', total_amount, 'Razorpay purchase')
        )

        return JSONResponse(content={
            'success': True,
            'payment_id': payment_id,
            'receipt_id': receipt_id,
            'receipt': {
                'id': db_receipt_id,
                'receipt_id': receipt_id,
                'total_amount': total_amount,
                'payment_method': 'razorpay',
                'payment_status': 'completed',
                'qr_code': qr_code,
                'items': order_items,
                'transaction_id': txn_id,
            }
        }), 200

    except Exception as e:
        print(f"Verify payment error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})


# ============================================================================
# 3. POST /direct-sale  –  Farmer Direct Sale (no Razorpay)
# ============================================================================

@payments_router.post('/direct-sale')
async def direct_sale(request: Request, user_id: str = Depends(get_current_user)):
    """Create a direct (offline) sale by farmer."""
    try:
        farmer_id = user_id
        data = await request.json()

        items = data.get('items', [])
        payment_type = data.get('payment_type', 'cash')  # cash | upi | card
        buyer_phone = data.get('buyer_phone', '')
        buyer_name = data.get('buyer_name', '')
        buyer_email = data.get('buyer_email', '')
        discount = float(data.get('discount', 0))

        if not items:
            return JSONResponse(status_code=400, content={'error': 'At least one item is required'})

        if payment_type not in ('cash', 'upi', 'card', 'online', 'bank_transfer'):
            return JSONResponse(status_code=400, content={'error': 'Invalid payment_type. Use cash, upi, card, or bank_transfer'})

        # --- Calculate totals ---
        subtotal = sum(
            float(it.get('quantity', 0)) * float(it.get('price_per_kg', 0))
            for it in items
        )
        total_amount = max(subtotal - discount, 0)

        # --- Try to find buyer by phone, else buyer_id = NULL ---
        buyer_id = None
        if buyer_phone:
            buyer_row = BaseModel.execute_query(
                "SELECT id FROM buyers WHERE phone = %s", (buyer_phone,), fetch_one=True
            )
            if buyer_row:
                buyer_id = buyer_row['id']

        # --- Create payment record ---
        payment_id = BaseModel.execute_insert(
            """INSERT INTO payments
               (buyer_id, amount, payment_method, status, created_at)
               VALUES (%s, %s, %s, %s, NOW())""",
            (buyer_id, total_amount, payment_type, 'completed')
        )

        # --- Create receipt ---
        receipt_id = _generate_receipt_id()
        qr_code = f"https://smartfarm.app/verify/{receipt_id}"

        db_receipt_id = BaseModel.execute_insert(
            """INSERT INTO receipts
               (receipt_id, payment_id, buyer_id, farmer_id,
                subtotal, discount, grand_total, payment_type, payment_status,
                buyer_name, buyer_phone, buyer_email, qr_code, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())""",
            (receipt_id, payment_id, buyer_id, farmer_id,
             subtotal, discount, total_amount, payment_type, 'completed',
             buyer_name, buyer_phone, buyer_email, qr_code)
        )

        # --- Create receipt items ---
        saved_items = []
        for it in items:
            item_total = float(it.get('quantity', 0)) * float(it.get('price_per_kg', 0))
            BaseModel.execute_insert(
                """INSERT INTO receipt_items
                   (receipt_id, product_id, product_name, quantity_kg, price_per_kg, product_quality, item_total)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (db_receipt_id, it.get('product_id'), it.get('product_name'),
                 float(it.get('quantity', 0)), float(it.get('price_per_kg', 0)),
                 it.get('quality', 'Standard'), item_total)
            )
            saved_items.append({
                'product_id': it.get('product_id'),
                'product_name': it.get('product_name'),
                'quantity': it.get('quantity'),
                'price_per_kg': it.get('price_per_kg'),
                'quality': it.get('quality', 'standard'),
                'total': item_total,
            })

        # --- Create transaction record ---
        txn_id = _generate_transaction_id()
        BaseModel.execute_insert(
            """INSERT INTO transactions
               (transaction_id, payment_id, receipt_id, user_id, user_type,
                type, amount, description, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())""",
            (txn_id, payment_id, db_receipt_id, farmer_id, 'farmer',
             'credit', total_amount, f'Direct sale to {buyer_name}')
        )

        # Get farmer info for receipt
        farmer_info = BaseModel.execute_query(
            "SELECT first_name, last_name, phone, email FROM farmers WHERE id = %s",
            (int(farmer_id),), fetch_one=True
        ) or {}
        farmer_name_full = f"{farmer_info.get('first_name', '')} {farmer_info.get('last_name', '')}".strip()

        return JSONResponse(content={
            'success': True,
            'receipt': {
                'id': db_receipt_id,
                'receipt_id': receipt_id,
                'farmer_id': farmer_id,
                'farmer_name': farmer_name_full,
                'farmer_phone': farmer_info.get('phone', ''),
                'farmer_email': farmer_info.get('email', ''),
                'buyer_name': buyer_name,
                'buyer_phone': buyer_phone,
                'buyer_email': buyer_email,
                'items': saved_items,
                'subtotal': subtotal,
                'discount': discount,
                'grand_total': total_amount,
                'payment_type': payment_type,
                'payment_status': 'completed',
                'qr_code': qr_code,
                'transaction_id': txn_id,
                'created_at': datetime.now().isoformat(),
            }
        }), 201

    except Exception as e:
        print(f"Direct sale error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})


# ============================================================================
# 4. GET /receipt/<receipt_id>  –  Get Receipt Details
# ============================================================================

@payments_router.get('/receipt/{receipt_id}')
async def get_receipt(receipt_id):
    """Return full receipt with items, buyer info, farmer info."""
    try:
        receipt = BaseModel.execute_query(
            """SELECT r.*,
                      f.first_name AS farmer_first_name, f.last_name AS farmer_last_name,
                      f.email AS farmer_email, f.phone AS farmer_phone,
                      b.first_name AS buyer_first_name, b.last_name AS buyer_last_name,
                      b.email AS buyer_email_db, b.phone AS buyer_phone_db
               FROM receipts r
               LEFT JOIN farmers f ON r.farmer_id = f.id
               LEFT JOIN buyers b ON r.buyer_id = b.id
               WHERE r.receipt_id = %s""",
            (receipt_id,), fetch_one=True
        )

        if not receipt:
            return JSONResponse(status_code=404, content={'error': 'Receipt not found'})

        # Get receipt items
        items = BaseModel.execute_query(
            "SELECT * FROM receipt_items WHERE receipt_id = %s",
            (receipt['id'],), fetch_all=True
        )

        receipt_data = _serialize_row(receipt)
        receipt_data['items'] = [_serialize_row(i) for i in (items or [])]

        return {'success': True, 'receipt': receipt_data}

    except Exception as e:
        print(f"Get receipt error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})


# ============================================================================
# 5. GET /receipt/<receipt_id>/pdf  –  Generate PDF (stub: returns JSON)
# ============================================================================

@payments_router.get('/receipt/{receipt_id}/pdf')
async def get_receipt_pdf(receipt_id):
    """Generate PDF for receipt. (Stub – returns JSON for now.)"""
    try:
        receipt = BaseModel.execute_query(
            "SELECT * FROM receipts WHERE receipt_id = %s",
            (receipt_id,), fetch_one=True
        )
        if not receipt:
            return JSONResponse(status_code=404, content={'error': 'Receipt not found'})

        items = BaseModel.execute_query(
            "SELECT * FROM receipt_items WHERE receipt_id = %s",
            (receipt['id'],), fetch_all=True
        )

        receipt_data = _serialize_row(receipt)
        receipt_data['items'] = [_serialize_row(i) for i in (items or [])]

        return {
            'success': True,
            'message': 'PDF generation coming soon. Returning JSON receipt data.',
            'receipt': receipt_data,
        }

    except Exception as e:
        print(f"Receipt PDF error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})


# ============================================================================
# 6. POST /receipt/<receipt_id>/send  –  Send Receipt (SMS / WhatsApp / Email)
# ============================================================================

@payments_router.post('/receipt/{receipt_id}/send')
async def send_receipt(receipt_id, request: Request):
    """Send receipt via SMS, WhatsApp and/or Email."""
    try:
        data = await request.json()
        send_sms = data.get('sms', False)
        send_whatsapp = data.get('whatsapp', False)
        send_email_flag = data.get('email', False)
        phone = data.get('phone', '').strip()
        email_address = data.get('email_address', '').strip()

        # Fetch receipt
        receipt = BaseModel.execute_query(
            "SELECT * FROM receipts WHERE receipt_id = %s",
            (receipt_id,), fetch_one=True
        )
        if not receipt:
            return JSONResponse(status_code=404, content={'error': 'Receipt not found'})

        # Fetch items
        items = BaseModel.execute_query(
            "SELECT * FROM receipt_items WHERE receipt_id = %s",
            (receipt['id'],), fetch_all=True
        ) or []

        # --- Format phone number to E.164 (India) ---
        def format_phone(p):
            p = p.replace(' ', '').replace('-', '')
            if p.startswith('+'):
                return p
            if p.startswith('0'):
                p = p[1:]
            if len(p) == 10:
                return f'+91{p}'
            return f'+{p}'

        formatted_phone = format_phone(phone) if phone else ''

        # Build plain-text receipt body
        item_lines = '\n'.join([
            f"  {it.get('product_name', 'Item')} – {it.get('quantity_kg', 0)} kg × ₹{it.get('price_per_kg', 0)}/kg = ₹{it.get('item_total', 0)}"
            for it in items
        ])
        grand_total = receipt.get('grand_total', 0)
        payment_type = receipt.get('payment_type', 'N/A')
        
        receipt_text = (
            f"🧾 SmartFarming Receipt\n"
            f"Receipt: {receipt_id}\n"
            f"Date: {receipt.get('created_at', '')}\n"
            f"---\n"
            f"{item_lines}\n"
            f"---\n"
            f"Subtotal: ₹{receipt.get('subtotal', 0)}\n"
            f"Discount: ₹{receipt.get('discount', 0)}\n"
            f"Grand Total: ₹{grand_total}\n"
            f"Payment: {payment_type}\n"
            f"Verify: https://smartfarm.app/verify/{receipt_id}"
        )

        results = {}

        # --- SMS via Twilio ---
        if send_sms:
            if not twilio_client or not TWILIO_PHONE:
                results['sms'] = {'sent': False, 'error': 'Twilio not configured'}
            elif not formatted_phone:
                results['sms'] = {'sent': False, 'error': 'Phone number required'}
            else:
                try:
                    msg = twilio_client.messages.create(
                        body=receipt_text,
                        from_=TWILIO_PHONE,
                        to=formatted_phone
                    )
                    print(f"[SMS] Sent to {formatted_phone}, SID: {msg.sid}")
                    results['sms'] = {'sent': True, 'sid': msg.sid}
                except Exception as sms_err:
                    print(f"[SMS ERROR] {sms_err}")
                    results['sms'] = {'sent': False, 'error': str(sms_err)}

        # --- WhatsApp via Twilio ---
        if send_whatsapp:
            if not twilio_client:
                results['whatsapp'] = {'sent': False, 'error': 'Twilio not configured'}
            elif not formatted_phone:
                results['whatsapp'] = {'sent': False, 'error': 'Phone number required'}
            else:
                try:
                    # Use Twilio WhatsApp sandbox number for testing
                    whatsapp_from = f'whatsapp:+14155238886'
                    whatsapp_to = f'whatsapp:{formatted_phone}'
                    msg = twilio_client.messages.create(
                        body=receipt_text,
                        from_=whatsapp_from,
                        to=whatsapp_to
                    )
                    print(f"[WhatsApp] Sent to {whatsapp_to}, SID: {msg.sid}")
                    results['whatsapp'] = {'sent': True, 'sid': msg.sid}
                except Exception as wa_err:
                    print(f"[WhatsApp ERROR] {wa_err}")
                    results['whatsapp'] = {'sent': False, 'error': str(wa_err)}

        # --- Email via SMTP ---
        if send_email_flag:
            if not email_address:
                results['email'] = {'sent': False, 'error': 'Email address required'}
            else:
                email_html = f"""
                <div style="font-family:Arial,sans-serif;max-width:520px;margin:auto;padding:24px;background:#f0fdf4;border-radius:12px;">
                    <h2 style="color:#166534;">🧾 SmartFarming Receipt</h2>
                    <p><strong>Receipt:</strong> {receipt_id}</p>
                    <p><strong>Date:</strong> {receipt.get('created_at', '')}</p>
                    <p><strong>Buyer:</strong> {receipt.get('buyer_name', '')}</p>
                    <hr/>
                    <table style="width:100%;border-collapse:collapse;">
                        <tr style="background:#dcfce7;">
                            <th style="padding:6px;text-align:left;">Item</th>
                            <th style="padding:6px;text-align:right;">Qty</th>
                            <th style="padding:6px;text-align:right;">Rate</th>
                            <th style="padding:6px;text-align:right;">Total</th>
                        </tr>
                        {''.join(
                            f"<tr><td style='padding:6px;'>{it.get('product_name','')}</td>"
                            f"<td style='padding:6px;text-align:right;'>{it.get('quantity_kg','')} kg</td>"
                            f"<td style='padding:6px;text-align:right;'>₹{it.get('price_per_kg','')}</td>"
                            f"<td style='padding:6px;text-align:right;'>₹{it.get('item_total','')}</td></tr>"
                            for it in items
                        )}
                    </table>
                    <hr/>
                    <p>Subtotal: ₹{receipt.get('subtotal', 0)}</p>
                    <p>Discount: ₹{receipt.get('discount', 0)}</p>
                    <p style="font-size:18px;"><strong>Grand Total: ₹{grand_total}</strong></p>
                    <p>Payment: {payment_type}</p>
                    <p style="font-size:12px;color:#6b7280;">
                        Verify: <a href="https://smartfarm.app/verify/{receipt_id}">https://smartfarm.app/verify/{receipt_id}</a>
                    </p>
                </div>
                """
                sent = _send_email(email_address, f'SmartFarming Receipt - {receipt_id}', email_html)
                if sent:
                    print(f"[Email] Sent to {email_address}")
                else:
                    print(f"[Email ERROR] Failed to send to {email_address}")
                results['email'] = {'sent': sent}

        return {'success': True, 'results': results}

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={'error': str(e)})


# ============================================================================
# 6b. POST /receipt/send-direct  –  Send Receipt via Email (no DB lookup)
# ============================================================================

@payments_router.post('/receipt/send-direct')
async def send_receipt_direct(request: Request):
    """Send receipt via email using receipt data from the request body.
    Used when the receipt was generated locally (not saved in DB)."""
    try:
        data = await request.json()
        email_address = data.get('email_address', '').strip()
        receipt = data.get('receipt_data', {})

        if not email_address:
            return JSONResponse(status_code=400, content={'error': 'Email address is required'})
        if not receipt:
            return JSONResponse(status_code=400, content={'error': 'Receipt data is required'})

        items = receipt.get('items', [])
        receipt_id = receipt.get('receipt_id', 'N/A')
        grand_total = receipt.get('grand_total', 0)
        subtotal_val = receipt.get('subtotal', 0)
        discount_val = receipt.get('discount', 0)
        payment_type = receipt.get('payment_type', 'N/A')
        buyer_name = receipt.get('buyer_name', '')
        farmer_name = receipt.get('farmer_name', '')
        created_at = receipt.get('created_at', '')

        # Build HTML email
        item_rows = ''.join(
            f"<tr><td style='padding:6px;'>{it.get('product_name','')}</td>"
            f"<td style='padding:6px;text-align:right;'>{it.get('quantity_kg','')} kg</td>"
            f"<td style='padding:6px;text-align:right;'>₹{it.get('price_per_kg','')}</td>"
            f"<td style='padding:6px;text-align:right;'>₹{it.get('item_total', float(it.get('quantity_kg',0))*float(it.get('price_per_kg',0)))}</td></tr>"
            for it in items
        )

        email_html = f"""
        <div style="font-family:'Segoe UI',Arial,sans-serif;max-width:520px;margin:auto;padding:0;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">
            <div style="background:linear-gradient(135deg,#f0fdf4,#dcfce7);padding:24px;text-align:center;">
                <div style="font-size:28px;margin-bottom:6px;">🌾</div>
                <h1 style="margin:0;font-size:22px;font-weight:700;color:#166534;">SmartFarming Receipt</h1>
                <p style="margin:4px 0 0;font-size:12px;color:#6b7280;">Your Trusted Farming Partner</p>
            </div>
            <div style="padding:24px;">
                <div style="background:#f0fdf4;padding:14px;border-radius:10px;margin-bottom:16px;">
                    <p style="margin:4px 0;font-size:13px;color:#374151;"><strong>Receipt:</strong> {receipt_id}</p>
                    <p style="margin:4px 0;font-size:13px;color:#374151;"><strong>Date:</strong> {created_at}</p>
                    <p style="margin:4px 0;font-size:13px;color:#374151;"><strong>Farmer:</strong> {farmer_name}</p>
                    <p style="margin:4px 0;font-size:13px;color:#374151;"><strong>Buyer:</strong> {buyer_name}</p>
                </div>
                <table style="width:100%;border-collapse:collapse;">
                    <tr style="background:#dcfce7;">
                        <th style="padding:8px;text-align:left;font-size:13px;color:#166534;">Item</th>
                        <th style="padding:8px;text-align:right;font-size:13px;color:#166534;">Qty</th>
                        <th style="padding:8px;text-align:right;font-size:13px;color:#166534;">Rate</th>
                        <th style="padding:8px;text-align:right;font-size:13px;color:#166534;">Total</th>
                    </tr>
                    {item_rows}
                </table>
                <hr style="border:none;border-top:1px solid #e5e7eb;margin:16px 0;"/>
                <p style="margin:4px 0;font-size:14px;color:#374151;">Subtotal: ₹{subtotal_val}</p>
                <p style="margin:4px 0;font-size:14px;color:#374151;">Discount: ₹{discount_val}</p>
                <p style="margin:8px 0 0;font-size:18px;font-weight:700;color:#166534;">Grand Total: ₹{grand_total}</p>
                <p style="margin:4px 0;font-size:13px;color:#6b7280;">Payment: {payment_type}</p>
            </div>
            <div style="background:#f9fafb;padding:16px;text-align:center;border-top:1px solid #e5e7eb;">
                <p style="margin:0;font-size:12px;color:#9ca3af;">Thank you for choosing SmartFarming! 🌱</p>
            </div>
        </div>
        """

        sent = await _send_email(email_address, f'SmartFarming Receipt - {receipt_id}', email_html)
        if sent:
            print(f"[Email] Direct receipt sent to {email_address}")
            return JSONResponse(content={'success': True, 'results': {'email': {'sent': True}}}), 200

        print(f"[Email ERROR] Failed to send direct receipt to {email_address}")
        return JSONResponse(
            content={
                'success': False,
                'error': 'Email delivery failed. Check SMTP settings (EMAIL_SENDER, EMAIL_PASSWORD).',
                'results': {'email': {'sent': False, 'error': 'SMTP send failed'}},
            },
            status_code=200,
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={'error': str(e)})


# ============================================================================
# 7. GET /transactions  –  User Transactions (JWT)
# ============================================================================

@payments_router.get('/transactions')
async def get_transactions(request: Request, user_id: str = Depends(get_current_user)):
    """Return all transactions for the logged-in user."""
    try:
        # user_id from dependency injection

        transactions = BaseModel.execute_query(
            """SELECT t.*,
                      r.receipt_id AS receipt_code
               FROM transactions t
               LEFT JOIN receipts r ON t.receipt_id = r.id
               WHERE t.buyer_id = %s OR t.farmer_id = %s
               ORDER BY t.created_at DESC""",
            (user_id, user_id), fetch_all=True
        )

        return {
            'success': True,
            'transactions': [_serialize_row(t) for t in (transactions or [])],
        }

    except Exception as e:
        print(f"Get transactions error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})


# ============================================================================
# 8. GET /buyer/purchase-history  –  Buyer Purchase History (JWT)
# ============================================================================

@payments_router.get('/buyer/purchase-history')
async def buyer_purchase_history(request: Request, user_id: str = Depends(get_current_user)):
    """Return all receipts where buyer_id = current user."""
    try:
        # user_id from dependency injection

        receipts = BaseModel.execute_query(
            """SELECT r.*,
                      f.first_name AS farmer_first_name, f.last_name AS farmer_last_name
               FROM receipts r
               LEFT JOIN farmers f ON r.farmer_id = f.id
               WHERE r.buyer_id = %s
               ORDER BY r.created_at DESC""",
            (user_id,), fetch_all=True
        )

        result = []
        for rec in (receipts or []):
            items = BaseModel.execute_query(
                "SELECT * FROM receipt_items WHERE receipt_id = %s",
                (rec['id'],), fetch_all=True
            )
            row = _serialize_row(rec)
            row['items'] = [_serialize_row(i) for i in (items or [])]
            result.append(row)

        return {'success': True, 'purchases': result}

    except Exception as e:
        print(f"Buyer purchase history error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})


# ============================================================================
# 9. GET /farmer/sales-history  –  Farmer Sales History (JWT)
# ============================================================================

@payments_router.get('/farmer/sales-history')
async def farmer_sales_history(request: Request, user_id: str = Depends(get_current_user)):
    """Return all receipts where farmer_id = current user."""
    try:
        # user_id from dependency injection

        receipts = BaseModel.execute_query(
            """SELECT r.*,
                      b.first_name AS buyer_first_name, b.last_name AS buyer_last_name
               FROM receipts r
               LEFT JOIN buyers b ON r.buyer_id = b.id
               WHERE r.farmer_id = %s
               ORDER BY r.created_at DESC""",
            (user_id,), fetch_all=True
        )

        result = []
        for rec in (receipts or []):
            items = BaseModel.execute_query(
                "SELECT * FROM receipt_items WHERE receipt_id = %s",
                (rec['id'],), fetch_all=True
            )
            row = _serialize_row(rec)
            row['items'] = [_serialize_row(i) for i in (items or [])]
            result.append(row)

        return {'success': True, 'sales': result}

    except Exception as e:
        print(f"Farmer sales history error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})
