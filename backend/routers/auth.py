from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database import get_db
from backend.models.user import User
from backend.security import limiter

router = APIRouter(prefix="/api/auth", tags=["Auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --- Schémas ---

class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str = ""


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict = {}


# --- Utils ---

def create_token(username: str, role: str, user_id: int = 0) -> str:
    return jwt.encode(
        {
            "sub": username,
            "role": role,
            "uid": user_id,
            "exp": datetime.utcnow() + timedelta(hours=24),
        },
        settings.api_secret_key,
        algorithm="HS256",
    )


# --- Routes ---

@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def admin_login(request: Request, req: LoginRequest):
    """Authentification admin."""
    if req.username != settings.admin_username:
        raise HTTPException(status_code=401, detail="Identifiants invalides")
    if not settings.admin_password_hash:
        raise HTTPException(status_code=500, detail="Admin non configuré")
    if not pwd_context.verify(req.password, settings.admin_password_hash):
        raise HTTPException(status_code=401, detail="Identifiants invalides")
    token = create_token(req.username, "admin")
    return TokenResponse(access_token=token, user={"username": req.username, "role": "admin"})


@router.post("/register", response_model=dict)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Inscription d'un nouveau candidat."""
    result = await db.execute(select(User).where(
        (User.username == req.username) | (User.email == req.email)
    ))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Nom d'utilisateur ou email déjà utilisé")

    user = User(
        username=req.username,
        email=req.email,
        password_hash=pwd_context.hash(req.password),
        full_name=req.full_name or req.username,
        role="candidate",
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    return {
        "message": "Compte créé avec succès",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
        },
    }


@router.post("/login/client", response_model=TokenResponse)
@limiter.limit("10/minute")
async def client_login(request: Request, req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Connexion candidat (utilisateurs enregistrés)."""
    result = await db.execute(select(User).where(User.username == req.username))
    user = result.scalar_one_or_none()
    if not user or not pwd_context.verify(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Identifiants invalides")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Compte désactivé")

    token = create_token(user.username, user.role, user.id)
    return TokenResponse(
        access_token=token,
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "level": getattr(user, "level", ""),
        },
    )
