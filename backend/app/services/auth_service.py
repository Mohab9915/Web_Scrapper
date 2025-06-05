"""
Authentication service using Supabase Auth.
"""
import os
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from supabase import Client
from datetime import datetime, timedelta
from uuid import UUID

from ..database import supabase
from ..models.auth import (
    UserSignUp, UserLogin, UserResponse, TokenResponse, 
    UserUpdate, ChangePasswordRequest, PasswordResetRequest
)

class AuthService:
    """Service for handling user authentication with Supabase Auth."""

    def __init__(self):
        self.supabase: Client = supabase

    async def sign_up(self, user_data: UserSignUp) -> TokenResponse:
        """
        Register a new user.

        Args:
            user_data (UserSignUp): User registration data

        Returns:
            TokenResponse: Authentication tokens and user data

        Raises:
            HTTPException: If registration fails
        """
        try:
            # Sign up user with Supabase Auth
            response = self.supabase.auth.sign_up({
                "email": user_data.email,
                "password": user_data.password,
                "options": {
                    "data": {
                        "name": user_data.name
                    }
                }
            })

            if response.user is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to create user account"
                )

            # Convert Supabase user to our UserResponse model
            user_response = UserResponse(
                id=UUID(response.user.id),
                email=response.user.email,
                name=response.user.user_metadata.get("name") if response.user.user_metadata else None,
                created_at=datetime.fromisoformat(response.user.created_at.replace('Z', '+00:00')),
                email_confirmed_at=datetime.fromisoformat(response.user.email_confirmed_at.replace('Z', '+00:00')) if response.user.email_confirmed_at else None
            )

            return TokenResponse(
                access_token=response.session.access_token,
                refresh_token=response.session.refresh_token,
                token_type="bearer",
                expires_in=response.session.expires_in,
                user=user_response
            )

        except Exception as e:
            if "already registered" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email already exists"
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Registration failed: {str(e)}"
            )

    async def sign_in(self, user_data: UserLogin) -> TokenResponse:
        """
        Authenticate user login.

        Args:
            user_data (UserLogin): User login credentials

        Returns:
            TokenResponse: Authentication tokens and user data

        Raises:
            HTTPException: If authentication fails
        """
        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": user_data.email,
                "password": user_data.password
            })

            if response.user is None or response.session is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )

            # Convert Supabase user to our UserResponse model
            user_response = UserResponse(
                id=UUID(response.user.id),
                email=response.user.email,
                name=response.user.user_metadata.get("name") if response.user.user_metadata else None,
                created_at=datetime.fromisoformat(response.user.created_at.replace('Z', '+00:00')),
                email_confirmed_at=datetime.fromisoformat(response.user.email_confirmed_at.replace('Z', '+00:00')) if response.user.email_confirmed_at else None
            )

            return TokenResponse(
                access_token=response.session.access_token,
                refresh_token=response.session.refresh_token,
                token_type="bearer",
                expires_in=response.session.expires_in,
                user=user_response
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

    async def sign_out(self, access_token: str) -> Dict[str, str]:
        """
        Sign out user and invalidate session.

        Args:
            access_token (str): User's access token

        Returns:
            Dict[str, str]: Success message

        Raises:
            HTTPException: If sign out fails
        """
        try:
            # Set the session for this request
            self.supabase.auth.set_session(access_token, "")
            
            # Sign out
            self.supabase.auth.sign_out()
            
            return {"message": "Successfully signed out"}

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Sign out failed: {str(e)}"
            )

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token (str): Refresh token

        Returns:
            TokenResponse: New authentication tokens and user data

        Raises:
            HTTPException: If token refresh fails
        """
        try:
            response = self.supabase.auth.refresh_session(refresh_token)

            if response.user is None or response.session is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )

            # Convert Supabase user to our UserResponse model
            user_response = UserResponse(
                id=UUID(response.user.id),
                email=response.user.email,
                name=response.user.user_metadata.get("name") if response.user.user_metadata else None,
                created_at=datetime.fromisoformat(response.user.created_at.replace('Z', '+00:00')),
                email_confirmed_at=datetime.fromisoformat(response.user.email_confirmed_at.replace('Z', '+00:00')) if response.user.email_confirmed_at else None
            )

            return TokenResponse(
                access_token=response.session.access_token,
                refresh_token=response.session.refresh_token,
                token_type="bearer",
                expires_in=response.session.expires_in,
                user=user_response
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token refresh failed"
            )

    async def get_current_user(self, access_token: str) -> UserResponse:
        """
        Get current user from access token.

        Args:
            access_token (str): User's access token

        Returns:
            UserResponse: Current user data

        Raises:
            HTTPException: If token is invalid or user not found
        """
        try:
            # Set the session for this request
            self.supabase.auth.set_session(access_token, "")
            
            # Get user
            response = self.supabase.auth.get_user()

            if response.user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token"
                )

            return UserResponse(
                id=UUID(response.user.id),
                email=response.user.email,
                name=response.user.user_metadata.get("name") if response.user.user_metadata else None,
                created_at=datetime.fromisoformat(response.user.created_at.replace('Z', '+00:00')),
                email_confirmed_at=datetime.fromisoformat(response.user.email_confirmed_at.replace('Z', '+00:00')) if response.user.email_confirmed_at else None
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )

    async def reset_password(self, email: str) -> Dict[str, str]:
        """
        Send password reset email.

        Args:
            email (str): User's email address

        Returns:
            Dict[str, str]: Success message

        Raises:
            HTTPException: If password reset fails
        """
        try:
            self.supabase.auth.reset_password_email(email)
            return {"message": "Password reset email sent"}

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password reset failed: {str(e)}"
            )
