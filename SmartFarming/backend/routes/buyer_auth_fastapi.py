"""
Buyer Authentication Routes (FastAPI)
Handles: Signup, OTP, Login, Password Reset
Path: /api/buyer-auth
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel as PydanticModel, EmailStr
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import random
import string
import json

from models.models import Buyer, OTP, BaseModel
from utils.jwt_utils import create_access_token

buyer_auth_router = APIRouter(prefix="/api/buyer-auth", tags=["Buyer Auth"])

# ============================================================================
# SCHEMAS
# ============================================================================

class SendOTPRequest(PydanticModel):
    phone: str
    type: str = "signup"  # "signup" or "login"

class VerifyOTPRequest(PydanticModel):
    phone: str
    otp: str

class BuyerSignupRequest(PydanticModel):
    phone: str
    email: str
    password: str
    location: str = ""
    district: str = ""
    first_name: str = ""
    last_name: str = ""
    name: str = ""

class BuyerLoginRequest(PydanticModel):
    phone: str
    password: str

# ============================================================================
# SEND OTP - For signup or login
# ============================================================================

@buyer_auth_router.post("/send-otp")
async def send_otp(request: SendOTPRequest):
    """
    Send OTP to buyer's phone number
    
    Request body:
    {
        "phone": "9876543210",
        "type": "signup" or "login"
    }
    
    Response:
    {
        "success": true,
        "message": "OTP sent to 9876****210",
        "otp_for_testing": "123456"  # Only in development
    }
    """
    try:
        phone = request.phone.strip()
        otp_type = request.type
        
        # Validate phone
        if not phone or len(phone) != 10 or not phone.isdigit():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid phone number"
            )
        
        # Generate OTP
        otp_code = ''.join(random.choices(string.digits, k=6))
        
        # Save OTP with 10-minute expiry
        otp_obj = OTP()
        otp_obj.save_otp(phone, otp_code, 'buyer', otp_type)
        
        # TODO: Send SMS via Twilio/AWS SNS
        # send_sms(phone, f"Your Smart Farming OTP is: {otp_code}")
        
        return {
            'success': True,
            'message': f'OTP sent to {phone[:4]}****{phone[-2:]}',
            'otp_for_testing': otp_code  # Remove in production
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERR] Send OTP error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP"
        )


# ============================================================================
# VERIFY OTP
# ============================================================================

@buyer_auth_router.post("/verify-otp")
async def verify_otp(request: VerifyOTPRequest):
    """
    Verify OTP code
    
    Request body:
    {
        "phone": "9876543210",
        "otp": "123456"
    }
    
    Response:
    {
        "success": true,
        "verification_token": "temp_token_xyz",
        "message": "OTP verified",
        "otp_type": "signup" or "login"
    }
    """
    try:
        phone = request.phone.strip()
        otp = request.otp.strip()
        
        # Validate inputs
        if not phone or not otp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone and OTP required"
            )
        
        # Verify OTP
        otp_obj = OTP()
        is_valid = otp_obj.verify_otp(phone, otp, 'buyer')
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired OTP"
            )
        
        # Get OTP type (signup or login)
        otp_type = otp_obj.get_otp_type(phone, 'buyer')
        
        # Create temporary verification token
        verification_token = create_access_token(
            identity=phone,
            additional_claims={'type': 'verification', 'otp_type': otp_type}
        )
        
        return {
            'success': True,
            'message': 'OTP verified successfully',
            'verification_token': verification_token,
            'otp_type': otp_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERR] Verify OTP error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OTP verification failed"
        )


# ============================================================================
# SIGNUP - Create buyer account
# ============================================================================

@buyer_auth_router.post("/signup", status_code=status.HTTP_201_CREATED)
async def buyer_signup(request: BuyerSignupRequest):
    """
    Create buyer account
    Frontend sends: name, email, phone, password, location, district, company_name
    """
    try:
        phone = request.phone.strip()
        email = request.email.strip()
        password = request.password.strip()
        location = request.location.strip()
        district = request.district.strip()
        
        # Support both 'name' and 'first_name' fields
        name = request.name.strip()
        first_name = request.first_name.strip() or name
        last_name = request.last_name.strip()
        
        # If name was provided as full name, split it
        if name and not last_name:
            parts = name.split(' ', 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ''
        
        # Combine location with district
        if district and location:
            location = f"{location}, {district}"
        
        # Validate required fields
        if not all([phone, first_name, email, password]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required fields"
            )
        
        # Validate email format
        if '@' not in email or '.' not in email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
        
        # Validate password strength (min 8 chars)
        if len(password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters"
            )
        
        # Check if buyer already exists
        existing = BaseModel.execute_query(
            "SELECT id FROM buyers WHERE phone = %s",
            (phone,),
            fetch_one=True
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Buyer with this phone already exists"
            )
        
        existing_email = BaseModel.execute_query(
            "SELECT id FROM buyers WHERE email = %s",
            (email,),
            fetch_one=True
        )
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Buyer with this email already exists"
            )
        
        # Hash password
        password_hash = generate_password_hash(password)
        
        # Create buyer account
        try:
            BaseModel.execute_query(
                """INSERT INTO buyers (phone, email, first_name, last_name, password_hash, location, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)""",
                (phone, email, first_name, last_name, password_hash, location)
            )
            # Retrieve the buyer ID
            buyer_data = BaseModel.execute_query(
                "SELECT id FROM buyers WHERE phone = %s",
                (phone,),
                fetch_one=True
            )
            buyer_id = buyer_data.get('id') if buyer_data else None
            
            if not buyer_id:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create account"
                )
        except HTTPException:
            raise
        except Exception as e:
            print(f"[ERR] Failed to create buyer: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create account"
            )
        
        # Create access token
        access_token = create_access_token(
            identity=str(buyer_id),
            additional_claims={'type': 'buyer', 'phone': phone}
        )
        
        # Build user object for frontend
        user_data = {
            'id': buyer_id,
            'buyer_id': buyer_id,
            'name': f"{first_name} {last_name}".strip(),
            'email': email,
            'phone': phone,
            'location': location,
            'role': 'buyer'
        }
        
        return {
            'success': True,
            'message': 'Account created successfully',
            'token': access_token,
            'access_token': access_token,
            'user': user_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERR] Signup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Signup failed"
        )


# ============================================================================
# LOGIN - Buyer login with credentials
# ============================================================================

@buyer_auth_router.post("/login")
async def buyer_login(request: BuyerLoginRequest):
    """
    Login buyer with phone and password
    
    Request body:
    {
        "phone": "9876543210",
        "password": "SecurePass123!"
    }
    
    Response:
    {
        "success": true,
        "buyer_id": 1,
        "access_token": "eyJ0eXAi...",
        "user": {
            "id": 1,
            "buyer_id": 1,
            "name": "Ramesh Kumar",
            "phone": "9876543210",
            "email": "ramesh@example.com",
            "role": "buyer"
        },
        "message": "Login successful"
    }
    """
    try:
        phone = request.phone.strip()
        password = request.password.strip()
        
        # Validate inputs
        if not phone or not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone and password required"
            )
        
        # Get buyer
        buyer = BaseModel.execute_query(
            "SELECT * FROM buyers WHERE phone = %s",
            (phone,),
            fetch_one=True
        )
        
        if not buyer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Buyer not found"
            )
        
        # Verify password
        try:
            if not check_password_hash(buyer.get('password_hash', ''), password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid password"
                )
        except Exception as pwd_err:
            print(f"[ERR] Password verification failed: {pwd_err}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password"
            )
        
        buyer_id = buyer.get('buyer_id') or buyer.get('id')
        
        # Create access token
        access_token = create_access_token(
            identity=str(buyer_id),
            additional_claims={'type': 'buyer', 'phone': phone}
        )
        
        return {
            'success': True,
            'message': 'Login successful',
            'token': access_token,
            'access_token': access_token,
            'buyer_id': buyer_id,
            'user': {
                'id': buyer_id,
                'buyer_id': buyer_id,
                'name': f"{buyer.get('first_name', '')} {buyer.get('last_name', '')}".strip(),
                'phone': phone,
                'email': buyer.get('email', ''),
                'role': 'buyer'
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERR] Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )
