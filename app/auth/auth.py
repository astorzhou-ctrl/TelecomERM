from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.auth.security import (
    verify_password,
    create_access_token,
    hash_password,
    decode_token
)

auth_router = APIRouter()
security = HTTPBearer()

# ✅ DEFAULT USER STORAGE (in-memory)
fake_user = {
    "username": "admin",
    "password": hash_password("admin123"),
    "role": "admin"   # ✅ standardized role
}

users = {
    "admin": fake_user
}


# =====================
# MODELS
# =====================

class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str


# =====================
# LOGIN
# =====================

@auth_router.post("/login")
def login(request: LoginRequest):
    user = users.get(request.username)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid username")

    if not verify_password(request.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid password")

    token = create_access_token({
        "sub": user["username"],
        "role": user["role"]
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }


# =====================
# REGISTER
# =====================

@auth_router.post("/register")
def register(request: RegisterRequest):

    if request.username in users:
        raise HTTPException(status_code=400, detail="User already exists")

    # ✅ Optional: normalize role input
    role = request.role.lower()

    if role not in ["admin", "risk_manager", "viewer"]:
        raise HTTPException(
            status_code=400,
            detail="Role must be one of: admin, risk_manager, viewer"
        )

    users[request.username] = {
        "username": request.username,
        "password": hash_password(request.password),
        "role": role
    }

    return {
        "message": "User registered successfully",
        "username": request.username,
        "role": role
    }


# =====================
# CURRENT USER (JWT)
# =====================

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    return payload


# =====================
# ROLE-BASED ACCESS CONTROL (RBAC)
# =====================

def require_role(allowed_roles: list):
    def role_checker(user: dict = Depends(get_current_user)):
        if user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Requires role: {allowed_roles}"
            )
        return user
    return role_checker