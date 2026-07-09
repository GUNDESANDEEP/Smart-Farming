"""
Authentication Routes (FastAPI) - Farmer/General Auth
Handles: Farmer Login, Farmer Signup, OTP, Password Reset
Path: /api/auth
"""

from fastapi import APIRouter, HTTPException, status, Depends
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
# UNIFIED LOGIN — handles farmer, buyer, admin (email OR phone)
# Frontend calls POST /api/auth/login for ALL roles
# OTP is only for registration, NOT login
# ============================================================================

from fastapi import Request as FastAPIRequest

@auth_router.post("/login")
async def unified_login(request: FastAPIRequest):
    """
    Unified login endpoint for all roles.
    
    Request body:
    {
        "role": "farmer" | "buyer" | "admin",
        "email": "user@example.com",   // optional
        "phone": "9876543210",          // optional
        "password": "password123"
    }
    
    - Farmer: login with email OR phone
    - Buyer: login with phone OR email; if email matches an admin, auto-elevates
    - Admin: login with email
    """
    try:
        data = await request.json()
        role = data.get('role', 'farmer')
        password = data.get('password', '')
        
        from fastapi.responses import JSONResponse
        
        if not password:
            return JSONResponse(content={'error': 'Password required'}, status_code=400)
        
        user = None
        
        if role == 'farmer':
            # Farmer: accept email OR phone
            email = (data.get('email', '') or '').strip()
            phone = (data.get('phone', '') or '').strip()
            if email:
                user = BaseModel.execute_query(
                    "SELECT * FROM farmers WHERE LOWER(email) = LOWER(%s)", (email,), fetch_one=True
                )
            if not user and phone:
                user = BaseModel.execute_query(
                    "SELECT * FROM farmers WHERE phone = %s", (phone,), fetch_one=True
                )
            if not user:
                return JSONResponse(
                    content={'error': 'No farmer account found. Please register first.'}, 
                    status_code=401
                )
                
        elif role == 'buyer':
            # Buyer: accept phone OR email
            phone_or_email = (data.get('phone', '') or data.get('email', '') or '').strip()
            if not phone_or_email:
                return JSONResponse(
                    content={'error': 'Phone or Email required for buyer login'}, 
                    status_code=400
                )
            
            if '@' in phone_or_email:
                # Looks like email — check ADMIN table FIRST (admin priority)
                admin_user = BaseModel.execute_query(
                    "SELECT *, admin_id as id FROM admins WHERE LOWER(email) = LOWER(%s)", 
                    (phone_or_email,), fetch_one=True
                )
                if admin_user:
                    user = admin_user
                    role = 'admin'  # Admin login via Buyer tab
                else:
                    # Not an admin — check buyers table
                    user = BaseModel.execute_query(
                        "SELECT * FROM buyers WHERE LOWER(email) = LOWER(%s)", (phone_or_email,), fetch_one=True
                    )
            else:
                # Looks like phone — query buyers by phone
                user = BaseModel.execute_query(
                    "SELECT * FROM buyers WHERE phone = %s", (phone_or_email,), fetch_one=True
                )
            
            if not user:
                return JSONResponse(
                    content={'error': 'No account found with this phone or email. Please register first.'}, 
                    status_code=401
                )
                
        elif role == 'admin':
            email = (data.get('email', '') or '').strip()
            if not email:
                return JSONResponse(
                    content={'error': 'Email required for admin login'}, 
                    status_code=400
                )
            user = BaseModel.execute_query(
                "SELECT *, admin_id as id FROM admins WHERE LOWER(email) = LOWER(%s)", 
                (email,), fetch_one=True
            )
            if not user:
                return JSONResponse(
                    content={'error': 'No admin account found with this email.'}, 
                    status_code=401
                )
        else:
            return JSONResponse(content={'error': 'Invalid role'}, status_code=400)
        
        # Verify password
        if not check_password_hash(user.get('password_hash', ''), password):
            return JSONResponse(
                content={'error': 'Incorrect password. Please try again.'}, 
                status_code=401
            )
        
        # Build response — direct login (no OTP)
        user_id = user.get('id') or user.get('admin_id')
        user_email = user.get('email', '')
        first_name = user.get('first_name', '') or user.get('name', '')
        last_name = user.get('last_name', '')
        name = f"{first_name} {last_name}".strip()
        
        identity = str(user_id)
        access_token = create_access_token(
            identity=identity, 
            additional_claims={'role': role, 'user_id': user_id, 'type': role}
        )
        
        # Create a simple refresh token (reuse access token logic with longer expiry)
        refresh_token = create_access_token(
            identity=identity,
            additional_claims={'type': 'refresh'}
        )
        
        return {
            'message': 'Login successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user_id,
                'name': name,
                'first_name': first_name,
                'last_name': last_name,
                'email': user_email,
                'phone': user.get('phone', ''),
                'role': role,
                'location': user.get('location', '')
            }
        }
        
    except Exception as e:
        print(f"[AUTH] Login error: {e}")
        import traceback
        traceback.print_exc()
        from fastapi.responses import JSONResponse
        error_str = str(e).lower()
        if 'connection' in error_str or 'timeout' in error_str or 'database' in error_str:
            return JSONResponse(
                content={'error': 'Server is warming up. Please try again in a moment.'},
                status_code=503
            )
        return JSONResponse(
            content={'error': 'Login failed. Please try again.'},
            status_code=500
        )

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


# ============================================================================
# NOTIFICATIONS ENDPOINTS
# ============================================================================

@auth_router.get("/notifications")
async def get_notifications(user_id: str = Depends(get_current_user)):
    """Get all notifications for the logged-in user, sorted by newest first"""
    try:
        notifications = BaseModel.execute_query(
            "SELECT * FROM notifications WHERE user_id = %s ORDER BY created_at DESC LIMIT 50",
            (int(user_id),),
            fetch_all=True
        ) or []
        serialized = []
        for n in notifications:
            serialized.append({
                'id': n['id'],
                'user_id': n['user_id'],
                'title': n['title'],
                'message': n['message'],
                'type': n.get('type', 'info'),
                'is_read': bool(n.get('is_read', False)),
                'action_url': n.get('action_url'),
                'created_at': n['created_at'].isoformat() if n.get('created_at') else None,
                'read_at': n['read_at'].isoformat() if n.get('read_at') else None,
                'data': n.get('data')
            })
        return serialized
    except Exception as e:
        print(f"[ERR] get_notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@auth_router.post("/notifications/read-all")
async def mark_all_notifications_read(user_id: str = Depends(get_current_user)):
    """Mark all notifications of the user as read"""
    try:
        BaseModel.execute_query(
            "UPDATE notifications SET is_read = TRUE, read_at = CURRENT_TIMESTAMP WHERE user_id = %s AND is_read = FALSE",
            (int(user_id),)
        )
        return {'success': True, 'message': 'All notifications marked as read'}
    except Exception as e:
        print(f"[ERR] mark_all_notifications_read: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@auth_router.post("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: int, user_id: str = Depends(get_current_user)):
    """Mark a specific notification as read"""
    try:
        BaseModel.execute_query(
            "UPDATE notifications SET is_read = TRUE, read_at = CURRENT_TIMESTAMP WHERE id = %s AND user_id = %s",
            (notification_id, int(user_id))
        )
        return {'success': True, 'message': 'Notification marked as read'}
    except Exception as e:
        print(f"[ERR] mark_notification_read: {e}")
        raise HTTPException(status_code=500, detail=str(e))
