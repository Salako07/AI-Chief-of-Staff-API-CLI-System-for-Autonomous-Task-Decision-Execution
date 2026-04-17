"""
FastAPI application entry point for AI Chief of Staff API.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Chief of Staff API",
    description="Intelligent task extraction, decision-making, and risk assessment system with async execution",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1", tags=["processing"])

# Root endpoint
@app.get("/")
def read_root():
    """Root endpoint with API information."""
    return {
        "service": "AI Chief of Staff API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 AI Chief of Staff API starting up...")

    # Initialize the processor
    try:
        from app.api.controller import init_process
        from crewai import LLM

        # Initialize LLM
        llm = LLM(model="gpt-4o-mini")
        logger.info("✅ LLM initialized successfully")

        # Initialize processor (tools and db are optional for API-only mode)
        init_process(llm=llm, tools=[], db=None)
        logger.info("✅ Processor initialized successfully")

    except Exception as e:
        logger.error(f"❌ Failed to initialize processor: {e}")
        logger.warning("⚠️ API will run but processing may fail")

    logger.info("📊 Docs available at: /docs")
    logger.info("✅ Health check at: /api/v1/health")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 AI Chief of Staff API shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
