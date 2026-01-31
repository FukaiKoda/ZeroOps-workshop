"""
ZeroOps Server - Main FastAPI Application

This is the entry point for the Server-Core.
Handles API routes, CORS, and initialization.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys
from pathlib import Path

# Add shared to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

from api.routes import router as api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="ZeroOps Workshop API",
    description="Backend for ZeroOps technical assessment platform",
    version="0.1.0",
)

# CORS middleware (allow client to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/v1")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "ZeroOps Server",
        "version": "0.1.0",
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "server": "ok",
        "worker": "ok",  # TODO: Check worker status
    }


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("🚀 ZeroOps Server starting up...")
    logger.info("   API documentation: http://localhost:8000/docs")
    logger.info("   Health check: http://localhost:8000/health")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("👋 ZeroOps Server shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
