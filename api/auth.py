"""Authentication endpoints and dependencies."""
import json
from fastapi import Cookie, HTTPException, Response
from typing import Optional
from models.auth import UserLogin

async def get_current_user(session: Optional[str] = Cookie(None)):
    """Dependency to get the current authenticated user."""
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return session

async def login(user_data: UserLogin):
    """Handle user login and set session cookie."""
    response = Response(
        content=json.dumps({"message": "Logged in successfully"}),
        media_type="application/json"
    )
    response.set_cookie(
        key="session",
        value=user_data.username,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        path="/"
    )
    return response

__all__ = ['login', 'get_current_user']
