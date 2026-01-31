from fastapi import FastAPI

app = FastAPI(title="ZeroOps Server")

@app.get("/")
async def root():
    return {"status": "ok", "message": "ZeroOps Server is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Dependency Injection Placeholder (for future endpoints)
from .core.database import db
from .api import endpoints

app.include_router(endpoints.router, prefix="/v1")


