"""
FastAPI backend service for ChatGPT Agent Mode crypto trading operations
through LangChain orchestration with Coinbase Advanced Trade API.
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog

from config import settings
from api_routes import router
from logger import setup_logging

# Setup structured logging
setup_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("Starting Coinbase LangChain Tool Server", version="1.0.0")
    yield
    logger.info("Shutting down Coinbase LangChain Tool Server")


# Create FastAPI application
app = FastAPI(
    title="Coinbase LangChain Tool Server",
    description="A tool server that enables ChatGPT Agent Mode to interact with Coinbase through LangChain orchestration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware for ChatGPT integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint providing service information."""
    return {
        "service": "Coinbase LangChain Tool Server",
        "version": "1.0.0",
        "description": "Tool server for ChatGPT Agent Mode crypto trading operations",
        "endpoints": {
            "docs": "/docs",
            "health": "/api/v1/health",
            "balance": "/api/v1/balance",
            "portfolio": "/api/v1/portfolio",
            "trade": "/api/v1/trade",
            "orders": "/api/v1/orders"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "coinbase-langchain-tool-server"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5000,
        reload=settings.DEBUG,
        log_level="info"
    )
