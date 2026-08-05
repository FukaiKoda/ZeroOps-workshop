from contextlib import asynccontextmanager
from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from .core.config import settings
from .core.rate_limit import limiter
from .core.db import create_tables
from .api import endpoints
from .api import auth as auth_router
from .api import repository as repo_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup."""
    await create_tables()
    yield


app = FastAPI(
    title="ZeroOps Server",
    description="ZeroOps Workshop Platform API",
    version="2.0.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "ZeroOps Server is running",
        "env": settings.DEBUG,
        "version": "2.0.0",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Routers
app.include_router(auth_router.router, prefix="/v1")
app.include_router(repo_router.router, prefix="/v1")
app.include_router(endpoints.router, prefix="/v1")
