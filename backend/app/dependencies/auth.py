"""
Authentication dependencies for FastAPI.
"""
import jwt
import os
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from uuid import UUID
from datetime import datetime

from ..services.auth_service import AuthService
from ..models.auth import UserResponse

# Security scheme for Bearer token (auto_error=False to handle errors manually)
security = HTTPBearer(auto_error=False)

async def get_auth_service() -> AuthService:
    """
    Dependency to get AuthService instance.

    Returns:
        AuthService: Authentication service instance
    """
    return AuthService()

def verify_jwt_token(token: str) -> dict:
    """
    Verify and decode JWT token from Supabase.

    Args:
        token: JWT token string

    Returns:
        dict: Decoded token payload

    Raises:
        HTTPException: If token is invalid
    """
    try:
        print(f"🔍 Verifying JWT token...")

        # For development, we'll decode without verification
        # In production, you should verify with Supabase's public key
        decoded = jwt.decode(token, options={"verify_signature": False})

        print(f"🔍 Decoded token: {decoded}")

        # Check if token is expired
        if 'exp' in decoded:
            exp_timestamp = decoded['exp']
            current_timestamp = datetime.utcnow().timestamp()
            print(f"🔍 Token expiry: {exp_timestamp}, current: {current_timestamp}")

            if current_timestamp > exp_timestamp:
                print("❌ Token has expired")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired"
                )

        print("✅ Token verification successful")
        return decoded
    except jwt.InvalidTokenError as e:
        print(f"❌ JWT decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> UserResponse:
    """
    Dependency to get the current authenticated user.

    Args:
        credentials: HTTP Bearer token credentials

    Returns:
        UserResponse: Current authenticated user

    Raises:
        HTTPException: If authentication fails
    """
    print(f"🔍 Authentication attempt - credentials present: {credentials is not None}")

    if not credentials:
        print("❌ No credentials provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    print(f"🔍 Token received: {credentials.credentials[:50]}...")

    try:
        # Verify the JWT token
        payload = verify_jwt_token(credentials.credentials)
        print(f"🔍 Token payload: {payload}")

        # Extract user information from token
        user_id = payload.get('sub')
        email = payload.get('email')

        print(f"🔍 Extracted user_id: {user_id}, email: {email}")

        if not user_id or not email:
            print("❌ Missing user_id or email in token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )

        # Create UserResponse from token data
        user_metadata = payload.get('user_metadata', {})

        user_response = UserResponse(
            id=UUID(user_id),
            email=email,
            name=user_metadata.get('name'),
            created_at=datetime.utcnow(),  # We don't have this in the token
            email_confirmed_at=datetime.utcnow() if payload.get('email_confirmed_at') else None
        )

        print(f"✅ Authentication successful for user: {email}")
        return user_response

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user_id(
    current_user: UserResponse = Depends(get_current_user)
) -> UUID:
    """
    Dependency to get the current user's ID.

    Args:
        current_user: Current authenticated user

    Returns:
        UUID: Current user's ID
    """
    return current_user.id

async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> Optional[UserResponse]:
    """
    Dependency to optionally get the current authenticated user.
    Returns None if no valid authentication is provided.
    
    Args:
        credentials: HTTP Bearer token credentials (optional)
        auth_service: Authentication service instance
        
    Returns:
        Optional[UserResponse]: Current authenticated user or None
    """
    if not credentials:
        return None
    
    try:
        user = await auth_service.get_current_user(credentials.credentials)
        return user
    except:
        return None
