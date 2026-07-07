from fastapi import APIRouter, Depends, HTTPException, Body, Request
from pydantic import BaseModel, EmailStr
from typing import Optional
from src.core.supabase_client import SupabaseManager
from src.core.auth_middleware import get_current_user_from_token

router = APIRouter(prefix="/auth", tags=["Authentication"])
manager = SupabaseManager()

class AuthRequest(BaseModel):
    email: EmailStr
    password: str

class ResetRequest(BaseModel):
    email: EmailStr

class UpdatePasswordRequest(BaseModel):
    password: str

@router.post("/register")
async def register(request: AuthRequest):
    result = manager.sign_up(request.email, request.password)
    if result.get("status") == "success":
        return {"status": "success", "message": "User registered successfully. Check your email for verification.", "user": result.get("user")}
    else:
        raise HTTPException(status_code=400, detail=result.get("message", "Registration failed"))

@router.post("/login")
async def login(request: AuthRequest):
    result = manager.sign_in(request.email, request.password)
    if result.get("status") == "success":
        return {"status": "success", "session": result.get("session"), "user": result.get("user")}
    else:
        raise HTTPException(status_code=401, detail=result.get("message", "Invalid credentials"))

@router.post("/reset")
async def reset_password(request: ResetRequest):
    result = manager.reset_password(request.email)
    if result.get("status") == "success":
        return {"status": "success", "message": "Password reset email sent."}
    else:
        raise HTTPException(status_code=400, detail=result.get("message", "Password reset failed"))

@router.put("/me")
async def update_me(request: UpdatePasswordRequest, current_user=Depends(get_current_user_from_token)):
    result = manager.update_password(request.password)
    if result.get("status") == "success":
        return {"status": "success", "message": "Password updated successfully"}
    else:
        raise HTTPException(status_code=400, detail=result.get("message", "Failed to update password"))

@router.get("/me")
async def get_me(current_user=Depends(get_current_user_from_token)):
    return current_user
