"""
Authentication Routes (FastAPI) - Farmer/General Auth
Handles: Farmer Login, Farmer Signup, OTP, Password Reset
Path: /api/auth
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel as PydanticModel
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import random
import string
import json

from models.models import Farmer, OTP, BaseModel
from utils.jwt_utils import create_access_token, get_current_user

auth_router = APIRouter(prefix="/api/auth", tags=["Auth"])

# ============================================================================
# SCHEMAS
# ============================================================================

class FarmerLoginRequest(PydanticModel):
    email: str
    password: str

class FarmerSignupRequest(PydanticModel):
    first_name: str
    last_name: str = ""
    email: str
    phone: str
    password: str
    location: str = ""
    district: str = ""
    farm_size: str = ""
    crops_grown: str = ""

class SignupRequest(PydanticModel):
    """Generic signup endpoint"""
    phone: str
    password: str
    role: str = "farmer"  # farmer, buyer, etc.
    first_name: str = ""
    last_name: str = ""
    email: str = ""

# ============================================================================
# FARMER LOGIN
# ============================================================================

@auth_router.post("/farmer-login")
async def farmer_login(request: FarmerLoginRequest):
    """
    Farmer login with email and password
    
    Request body:
    {
        "email": "farmer@example.com",
        "password": "SecurePass123!"
    }
    
    Response:
    {
        "success": true,
        "token": "JWT_TOKEN",
        "access_token": "JWT_TOKEN",
        "farmer_id": 1,
        "user": {
            "id": 1,
            "farmer_id": 1,
            "name": "John Farmer",
            "email": "farmer@example.com",
            "phone": "9876543210",
            "role": "farmer"
        }
    }
    """
    try:
        email = request.email.strip()
        password = request.password.strip()
        
        if not email or not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email and password are required"
            )
        
        # Get farmer from database
        farmer_data = BaseModel.execute_query(
            "SELECT * FROM farmers WHERE email = %s",
            (email,),
            fetch_one=True
        )
        
        if not farmer_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        password_hash = farmer_data.get('password_hash', '')
        
        try:
            if not check_password_hash(password_hash, password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
        except Exception as pwd_err:
            print(f"[ERR] Password check failed: {pwd_err}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Create JWT token
        farmer_id = farmer_data.get('id')
        access_token = create_access_token(
            identity=str(farmer_id),
            additional_claims={'type': 'farmer'}
        )
        
        return {
            'success': True,
            'token': access_token,
            'access_token': access_token,
            'farmer_id': farmer_id,
            'user': {
                'id': farmer_id,
                'farmer_id': farmer_id,
                'name': f"{farmer_data.get('first_name', '')} {farmer_data.get('last_name', '')}".strip(),
                'email': email,
                'phone': farmer_data.get('phone', ''),
                'role': 'farmer'
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERR] Farmer login error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


# ============================================================================
# FARMER SIGNUP
# ============================================================================

@auth_router.post("/farmer-signup", status_code=status.HTTP_201_CREATED)
async def farmer_signup(request: FarmerSignupRequest):
    """
    Create farmer account
    
    Request body:
    {
        "first_name": "John",
        "last_name": "Farmer",
        "email": "john@farm.com",
        "phone": "9876543210",
        "password": "SecurePass123!",
        "location": "Bangalore",
        "district": "Bangalore",
        "farm_size": "5 acres",
        "crops_grown": "Tomatoes, Onions"
    }
    
    Response:
    {
        "success": true,
        "message": "Account created successfully",
        "token": "JWT_TOKEN",
        "farmer_id": 1,
        "user": {...}
    }
    """
    try:
        first_name = request.first_name.strip()
        last_name = request.last_name.strip()
        email = request.email.strip()
        phone = request.phone.strip()
        password = request.password.strip()
        location = request.location.strip()
        district = request.district.strip()
        
        # Validate required fields
        if not all([first_name, email, phone, password]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="first_name, email, phone, and password are required"
            )
        
        # Validate email format
        if '@' not in email or '.' not in email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
        
        # Validate phone format
        if not phone.isdigit() or len(phone) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid phone number"
            )
        
        # Validate password strength
        if len(password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters"
            )
        
        # Check if farmer already exists
        farmer = Farmer()
        existing_email = farmer.get_farmer_by_email(email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Farmer with this email already exists"
            )
        
        existing_phone = farmer.get_farmer_by_phone(phone)
        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Farmer with this phone already exists"
            )
        
        # Hash password
        password_hash = generate_password_hash(password)
        
        # Combine location with district
        full_location = location
        if district and location:
            full_location = f"{location}, {district}"
        elif district:
            full_location = district
        
        # Create farmer account using direct query
        try:
            BaseModel.execute_query(
                """INSERT INTO farmers (first_name, last_name, email, phone, password_hash, location, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)""",
                (first_name, last_name, email, phone, password_hash, full_location)
            )
            # Retrieve the farmer ID
            farmer_data = BaseModel.execute_query(
                "SELECT id FROM farmers WHERE email = %s",
                (email,),
                fetch_one=True
            )
            farmer_id = farmer_data.get('id') if farmer_data else None
            
            if not farmer_id:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create account"
                )
        except HTTPException:
            raise
        except Exception as e:
            print(f"[ERR] Failed to create farmer: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create account"
            )
        
        # Create access token
        access_token = create_access_token(
            identity=str(farmer_id),
            additional_claims={'type': 'farmer'}
        )
        
        return {
            'success': True,
            'message': 'Account created successfully',
            'token': access_token,
            'access_token': access_token,
            'farmer_id': farmer_id,
            'user': {
                'id': farmer_id,
                'farmer_id': farmer_id,
                'name': f"{first_name} {last_name}".strip(),
                'email': email,
                'phone': phone,
                'location': full_location,
                'role': 'farmer'
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERR] Farmer signup error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Signup failed: {str(e)}"
        )


# ============================================================================
# GENERIC SIGNUP - Support both farmer and buyer signup
# ============================================================================

@auth_router.post("/signup", status_code=status.HTTP_201_CREATED)
async def generic_signup(request: SignupRequest):
    """
    Generic signup endpoint that supports multiple roles
    
    Request body:
    {
        "phone": "9876543210",
        "password": "SecurePass123!",
        "role": "farmer" or "buyer",
        "first_name": "John",
        "email": "john@example.com"
    }
    """
    try:
        phone = request.phone.strip()
        password = request.password.strip()
        role = request.role.strip().lower()
        first_name = request.first_name.strip()
        email = request.email.strip()
        
        # Validate required fields
        if not all([phone, password, first_name, email]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="phone, password, first_name, and email are required"
            )
        
        if role not in ['farmer', 'buyer']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="role must be 'farmer' or 'buyer'"
            )
        
        # Route to appropriate signup
        if role == 'farmer':
            farmer = Farmer()
            
            # Check if farmer already exists
            existing_email = farmer.get_farmer_by_email(email)
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Farmer with this email already exists"
                )
            
            # Hash password
            password_hash = generate_password_hash(password)
            
            # Create farmer account
            try:
                BaseModel.execute_query(
                    """INSERT INTO farmers (first_name, last_name, email, phone, password_hash, created_at)
                       VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)""",
                    (first_name, request.last_name.strip(), email, phone, password_hash)
                )
                # Retrieve the farmer ID
                farmer_data = BaseModel.execute_query(
                    "SELECT id FROM farmers WHERE email = %s",
                    (email,),
                    fetch_one=True
                )
                farmer_id = farmer_data.get('id') if farmer_data else None
                
                if not farmer_id:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to create account"
                    )
            except HTTPException:
                raise
            except Exception as e:
                print(f"[ERR] Failed to create farmer: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create account"
                )
            
            # Create access token
            access_token = create_access_token(
                identity=str(farmer_id),
                additional_claims={'type': 'farmer'}
            )
            
            return {
                'success': True,
                'message': 'Farmer account created successfully',
                'token': access_token,
                'farmer_id': farmer_id,
                'user': {
                    'id': farmer_id,
                    'farmer_id': farmer_id,
                    'name': first_name,
                    'email': email,
                    'phone': phone,
                    'role': 'farmer'
                }
            }
        
        # If buyer signup needed, can be added here
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Buyer signup should use /buyer-auth/signup"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERR] Generic signup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Signup failed: {str(e)}"
        )
