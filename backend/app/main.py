from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api import tasks, voice, websocket
from app.core.database import create_tables
from app.core.logging import configure_logging_from_env, get_logger
import os

# Configure logging first
configure_logging_from_env()
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Task Reminder API",
    description="A minimalist task reminder application with voice interaction",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tasks.router)
app.include_router(voice.router)
app.include_router(websocket.router)

@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    logger.info("Starting Task Reminder API...")
    
    # Create database tables
    try:
        create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise
    
    # Check for required environment variables
    required_env_vars = ["ANTHROPIC_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {missing_vars}")
        logger.warning("Some features may not work properly")
    else:
        logger.info("All required environment variables are present")
    
    # Log configuration
    logger.info(f"CORS origins: {os.getenv('CORS_ORIGINS', 'Not configured')}")
    logger.info(f"Kokoro TTS URL: {os.getenv('KOKORO_BASE_URL', 'Not configured')}")
    logger.info(f"TTS default voice: {os.getenv('TTS_DEFAULT_VOICE', 'Not configured')}")
    
    logger.info("Task Reminder API started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Task Reminder API...")
    logger.info("Task Reminder API shutdown complete")

@app.get("/")
async def root():
    """Root endpoint"""
    logger.debug("Root endpoint accessed")
    return {
        "message": "Task Reminder API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.debug("Health check endpoint accessed")
    return {
        "status": "healthy",
        "message": "Task Reminder API is running"
    }

# Serve static files (for frontend)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")
    logger.info("Static files mounted at /static")

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )