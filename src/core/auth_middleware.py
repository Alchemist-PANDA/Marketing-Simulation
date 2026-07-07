from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
from src.core.auth_utils import is_auth_enabled, get_local_user
from src.core.supabase_client import SupabaseManager

security = HTTPBearer(auto_error=False)

def get_current_user_from_token(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> Dict[str, Any]:
    """
    FastAPI Dependency to retrieve the current user from a JWT token.
    Raises HTTPException if the token is invalid and auth is enforced.
    """
    if not is_auth_enabled():
        return get_local_user()

    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated. Bearer token missing.")

    token = credentials.credentials
    manager = SupabaseManager()
    
    try:
        user_response = manager.get_user(token)
        if user_response.get("status") == "success":
            user_data = user_response.get("user", {})
            return {
                "id": user_data.id if hasattr(user_data, "id") else user_data.get("id"),
                "email": user_data.email if hasattr(user_data, "email") else user_data.get("email"),
                "is_authenticated": True,
                "mode": "supabase",
                # Mock plan retrieval. In a real scenario, fetch from profiles table.
                "plan": "free" 
            }
        else:
            raise HTTPException(status_code=401, detail=user_response.get("message", "Invalid token"))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

def require_role(allowed_roles: list[str]):
    """
    Dependency factory to check if the user has one of the allowed roles.
    Usage: @app.get("/premium", dependencies=[Depends(require_role(["pro", "enterprise"]))])
    """
    def role_checker(user: Dict[str, Any] = Depends(get_current_user_from_token)):
        if user.get("mode") == "local":
            return user
            
        user_plan = user.get("plan", "free")
        if user_plan not in allowed_roles and "admin" not in allowed_roles:
            raise HTTPException(status_code=403, detail=f"Access denied. Requires one of: {', '.join(allowed_roles)}")
        return user
        
    return role_checker
