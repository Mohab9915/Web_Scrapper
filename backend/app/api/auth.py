"""
Authentication API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict

from ..models.auth import (
    UserSignUp, UserLogin, TokenResponse, UserResponse, 
    RefreshTokenRequest, PasswordResetRequest, UserUpdate,
    ChangePasswordRequest
)
from ..services.auth_service import AuthService
from ..dependencies.auth import get_current_user, get_auth_service

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/signup", response_model=TokenResponse)
async def sign_up(
    user_data: UserSignUp,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register a new user account.
    
    Args:
        user_data: User registration data
        auth_service: Authentication service
        
    Returns:
        TokenResponse: Authentication tokens and user data
    """
    return await auth_service.sign_up(user_data)

@router.post("/signin", response_model=TokenResponse)
async def sign_in(
    user_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Authenticate user login.
    
    Args:
        user_data: User login credentials
        auth_service: Authentication service
        
    Returns:
        TokenResponse: Authentication tokens and user data
    """
    return await auth_service.sign_in(user_data)

@router.post("/signout")
async def sign_out(
    current_user: UserResponse = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Sign out current user.
    
    Args:
        current_user: Current authenticated user
        auth_service: Authentication service
        
    Returns:
        Dict: Success message
    """
    # Note: In a real implementation, you'd need to get the access token
    # For now, we'll just return a success message
    return {"message": "Successfully signed out"}

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Refresh access token using refresh token.
    
    Args:
        refresh_data: Refresh token data
        auth_service: Authentication service
        
    Returns:
        TokenResponse: New authentication tokens and user data
    """
    return await auth_service.refresh_token(refresh_data.refresh_token)

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get current user profile.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        UserResponse: Current user data
    """
    return current_user

@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordResetRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Send password reset email.
    
    Args:
        reset_data: Password reset request data
        auth_service: Authentication service
        
    Returns:
        Dict: Success message
    """
    return await auth_service.reset_password(reset_data.email)

@router.put("/profile", response_model=UserResponse)
async def update_profile(
    profile_data: UserUpdate,
    current_user: UserResponse = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Update user profile.
    
    Args:
        profile_data: Profile update data
        current_user: Current authenticated user
        auth_service: Authentication service
        
    Returns:
        UserResponse: Updated user data
    """
    # For now, just return the current user
    # In a full implementation, you'd update the user profile
    return current_user
