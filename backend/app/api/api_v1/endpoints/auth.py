"""
Authentication endpoints
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """User login endpoint"""
    # TODO: Implement actual authentication logic
    return LoginResponse(
        access_token="dummy-token",
        token_type="bearer",
        expires_in=900
    )


@router.post("/logout")
async def logout():
    """User logout endpoint"""
    # TODO: Implement logout logic (token blacklisting)
    return {"message": "Successfully logged out"}