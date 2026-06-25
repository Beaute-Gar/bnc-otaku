from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from slowapi import Limiter
from slowapi.util import get_remote_address
from itsdangerous import URLSafeTimedSerializer
from backend.config import settings
from backend.database import get_db
from backend.models.user import User

# --- Rate Limiting (slowapi) ---
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.api_rate_limit])

# --- CSRF Token ---
csrf_serializer = URLSafeTimedSerializer(secret_key=settings.csrf_secret, salt="bnc-csrf")


def generate_csrf_token() -> str:
    return csrf_serializer.dumps("csrf")


def verify_csrf_token(token: str, max_age: int = 3600) -> bool:
    try:
        csrf_serializer.loads(token, max_age=max_age)
        return True
    except Exception:
        return False


# --- JWT Auth ---
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentification requise")
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.api_secret_key,
            algorithms=["HS256"],
        )
        username = payload.get("sub")
        role = payload.get("role")
        if not username or role == "admin":
            raise HTTPException(status_code=401, detail="Token invalide")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable ou désactivé")
    return user
