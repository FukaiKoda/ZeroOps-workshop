from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from .core.config import settings
from .core.rate_limit import limiter
from .api import endpoints

app = FastAPI(title="ZeroOps Server")


@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "ZeroOps Server is running",
        "env": settings.DEBUG,
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.include_router(endpoints.router, prefix="/v1")
