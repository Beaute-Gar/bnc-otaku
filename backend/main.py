"""
BNC-OTAKU - Backend FastAPI
Point d'entrée de l'application.
Orchestre les routers, la DB, les bots, et le dashboard temps réel.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.config import settings
from backend.database import init_db, async_session_factory
from backend.security import limiter
from backend.routers import quiz, auth, webhooks, certificate, payment
from backend.services.payment_service import seed_products


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager : init DB au démarrage, cleanup à l'arrêt."""
    await init_db()
    async with async_session_factory() as session:
        await seed_products(session)
        await session.commit()
    yield
    # Arrêt (cleanup si nécessaire)


app = FastAPI(
    title="BNC-Otaku API",
    description="Bureau National de Certification Otaku - Backend API",
    version="1.0.0",
    lifespan=lifespan,
)

# --- Rate Limiting ---
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers (d'abord, pour priorité sur les routes API) ---
app.include_router(quiz.router)
app.include_router(auth.router)
app.include_router(webhooks.router)
app.include_router(certificate.router)
app.include_router(payment.router)


@app.get("/")
async def root():
    return {
        "service": "BNC-Otaku API",
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


# --- Fichiers statiques (frontend) - DOIT être APRÈS les routes API ---
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
