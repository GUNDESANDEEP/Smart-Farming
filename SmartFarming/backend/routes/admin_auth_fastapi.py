"""
Admin Authentication Routes (FastAPI)
Handles: Login, Logout, Password change, Token verification
Path: /api/admin-auth
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel as PydanticModel
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
import json

from models.models import Admin, BaseModel
from utils.jwt_utils import create_access_token, get_current_user

admin_auth_router = APIRouter(prefix="/api/admin-auth", tags=["Admin Auth"])

# ============================================================================
# SCHEMAS
# ============================================================================

class AdminLoginRequest(PydanticModel):
    email: str
    password: str

class PasswordChangeRequest(PydanticModel):
    current_password: str
    new_password: str

# ============================================================================
# LOGIN - Admin login with email and password
# ============================================================================

@admin_auth_router.post("/login")
async def admin_login(request: AdminLoginRequest):
    """
    Admin login with email and password
    
    Request body:
    {
        "email": "admin@smartfarming.com",
        "password": "admin123"
    }
    
    Response:
    {
        "success": true,
        "token": "JWT_TOKEN",
        "access_token": "JWT_TOKEN",
        "admin_id": 1,
        "user": {
            "id": 1,
            "admin_id": 1,
            "name": "Admin",
            "email": "admin@smartfarming.com",
            "role": "admin",
            "admin_role": "super_admin"
        }
    }
    """
    try:
        email = request.email.strip()
        password = request.password
        
        if not email or not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email and password are required"
            )
        
        # Get admin from database
        admin_data = BaseModel.execute_query(
            "SELECT * FROM admins WHERE email = %s",
            (email,),
            fetch_one=True
        )
        
        if not admin_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        password_hash = admin_data.get('password_hash', '')
        
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
        
        # Update last login
        admin_id = admin_data.get('admin_id')
        try:
            BaseModel.execute_query(
                "UPDATE admins SET last_login = CURRENT_TIMESTAMP WHERE admin_id = %s",
                (admin_id,)
            )
        except Exception as e:
            print(f"[WARN] Failed to update last login: {e}")
        
        # Create JWT token
        access_token = create_access_token(
            identity=str(admin_id),
            additional_claims={'role': admin_data.get('role', 'moderator')}
        )
        
        return {
            'success': True,
            'token': access_token,
            'access_token': access_token,
            'admin_id': admin_id,
            'user': {
                'id': admin_id,
                'admin_id': admin_id,
                'name': admin_data.get('first_name', 'Admin'),
                'email': email,
                'role': 'admin',
                'admin_role': admin_data.get('role', 'moderator')
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERR] Admin login error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


# ============================================================================
# LOGOUT - Admin logout
# ============================================================================

@admin_auth_router.post("/logout")
async def admin_logout(admin_id: str = Depends(get_current_user)):
    """
    Admin logout (client-side cleanup of token)
    
    Response:
    {
        "success": true,
        "message": "Logged out successfully"
    }
    """
    try:
        # Log the logout action
        try:
            BaseModel.execute_query(
                """INSERT INTO audit_logs (admin_id, action, entity_type, entity_id, created_at) 
                   VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)""",
                (admin_id, 'logout', 'auth', None)
            )
        except Exception as e:
            print(f"[WARN] Failed to log logout action: {e}")
        
        return {
            'success': True,
            'message': 'Logged out successfully'
        }
        
    except Exception as e:
        print(f"[ERR] Logout error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


# ============================================================================
# VERIFY TOKEN - Check if admin token is valid
# ============================================================================

@admin_auth_router.get("/verify-token")
async def admin_verify_token(admin_id: str = Depends(get_current_user)):
    """
    Verify if JWT token is valid
    Requires Authorization header with Bearer token
    
    Response:
    {
        "success": true,
        "message": "Token is valid",
        "admin_id": 1,
        "role": "super_admin"
    }
    """
    try:
        return {
            'success': True,
            'message': 'Token is valid',
            'admin_id': admin_id,
            'role': 'moderator'
        }
        
    except Exception as e:
        print(f"[ERR] Token verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


# ============================================================================
# CHANGE PASSWORD
# ============================================================================

@admin_auth_router.put("/change-password")
async def admin_change_password(
    request: PasswordChangeRequest,
    admin_id: str = Depends(get_current_user)
):
    """
    Change admin password
    
    Request body:
    {
        "current_password": "OldPass123!",
        "new_password": "NewPass123!"
    }
    
    Response:
    {
        "success": true,
        "message": "Password changed successfully"
    }
    """
    try:
        current_password = request.current_password.strip()
        new_password = request.new_password.strip()
        
        # Validate inputs
        if not current_password or not new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both passwords required"
            )
        
        if len(new_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters"
            )
        
        if current_password == new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from current"
            )
        
        # Get admin
        admin_data = BaseModel.execute_query(
            "SELECT * FROM admins WHERE admin_id = %s",
            (admin_id,),
            fetch_one=True
        )
        
        if not admin_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found"
            )
        
        # Verify current password
        if not check_password_hash(admin_data.get('password_hash', ''), current_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect"
            )
        
        # Hash new password
        new_password_hash = generate_password_hash(new_password)
        
        # Update password
        try:
            BaseModel.execute_query(
                "UPDATE admins SET password_hash = %s WHERE admin_id = %s",
                (new_password_hash, admin_id)
            )
        except Exception as e:
            print(f"[ERR] Failed to update password: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to change password"
            )
        
        # Log action
        try:
            BaseModel.execute_query(
                """INSERT INTO audit_logs (admin_id, action, entity_type, entity_id, created_at) 
                   VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)""",
                (admin_id, 'password_change', 'auth', admin_id)
            )
        except Exception as e:
            print(f"[WARN] Failed to log password change: {e}")
        
        return {
            'success': True,
            'message': 'Password changed successfully'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERR] Change password error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


# ============================================================================
# GET ADMIN PROFILE
# ============================================================================

@admin_auth_router.get("/profile")
async def admin_get_profile(admin_id: str = Depends(get_current_user)):
    """
    Get current admin profile
    
    Response:
    {
        "success": true,
        "profile": {
            "admin_id": 1,
            "email": "admin@smartfarming.com",
            "first_name": "Super",
            "last_name": "Admin",
            "role": "super_admin",
            "permissions": [...],
            "last_login": "2026-06-03T10:30:00",
            "is_active": true
        }
    }
    """
    try:
        admin_data = BaseModel.execute_query(
            "SELECT * FROM admins WHERE admin_id = %s",
            (admin_id,),
            fetch_one=True
        )
        
        if not admin_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found"
            )
        
        # Parse permissions if JSON
        permissions = admin_data.get('permissions', [])
        if isinstance(permissions, str):
            try:
                permissions = json.loads(permissions)
            except:
                permissions = []
        
        return {
            'success': True,
            'profile': {
                'admin_id': admin_data.get('admin_id'),
                'email': admin_data.get('email'),
                'first_name': admin_data.get('first_name'),
                'last_name': admin_data.get('last_name', ''),
                'role': admin_data.get('role', 'moderator'),
                'permissions': permissions,
                'last_login': admin_data.get('last_login'),
                'is_active': admin_data.get('is_active', True)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERR] Get profile error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get profile"
        )
