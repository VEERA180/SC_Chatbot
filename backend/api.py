"""
FastAPI server for CRM AI Assistant
Provides REST API endpoints for the React frontend
"""
import asyncio
import sys
import os
from pathlib import Path
import time
import uuid
from contextvars import ContextVar

# Add current directory to Python path BEFORE any local imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Load environment variables
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Now import local modules
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn

# Import your modules
from core.config import load_config
from core.logging_config import RAGLogger, set_correlation_id, get_correlation_id
from core.exceptions import RAGException
from rag_orchestrator import RAGOrchestrator

# Initialize FastAPI app
app = FastAPI(
    title="SCORE AI Assistant Prod API",
    description="RAG-based chatbot for score work items",
    version="1.0.0"
)

# CORS configuration - allow React frontend (local + production)
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # Old URL (kept for reference):
    # "https://scoreaiassistant-prod-frontend.azurewebsites.net",
    "https://scorefrontend-cthtdedfgjadewcm.westeurope-01.azurewebsites.net",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request tracking middleware
class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """Middleware to add correlation ID and log request timing"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate or get correlation ID from header
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        set_correlation_id(correlation_id)
        
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Log request details
        if logger:
            logger.info(
                f"Request completed",
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2)
                }
            )
        
        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response


# Add request tracking middleware
app.add_middleware(RequestTrackingMiddleware)


# Global variables for app state
rag_app = None
logger = None


# Request/Response models
class ChatRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = "default"
    user_id: Optional[str] = "anonymous"


class SourceItem(BaseModel):
    id: str
    type: str
    title: str
    url: Optional[str] = None
    hierarchy_path: Optional[str] = None
    state: Optional[str] = None
    assigned_to: Optional[str] = None
    has_comments: Optional[bool] = False
    epicId: Optional[str] = None
    epicTitle: Optional[str] = None
    epicUrl: Optional[str] = None
    featureId: Optional[str] = None
    featureTitle: Optional[str] = None
    featureUrl: Optional[str] = None
    storyId: Optional[str] = None
    storyTitle: Optional[str] = None
    storyUrl: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    type: str
    sources: List[Dict[str, Any]] = []
    top_sources_formatted: Optional[str] = ""  # ✅ ADD THIS LINE
    error: Optional[str] = None


class SessionStats(BaseModel):
    created_at: Optional[str] = None
    turn_count: int = 0


@app.on_event("startup")
async def startup_event():
    """Initialize the RAG application on startup"""
    global rag_app, logger
    
    # Load configuration
    config = load_config()
    
    # Configure logging with JSON format for production
    log_dir = Path(__file__).parent.parent / "logs"
    log_format = os.getenv("LOG_FORMAT", "text")  # 'json' for production, 'text' for local
    
    RAGLogger.configure(
        log_level=config.log_level,
        log_dir=log_dir,
        log_format=log_format
    )
    
    logger = RAGLogger.get_logger(__name__)
    logger.info("=" * 80)
    logger.info("SCORE AI Assistant API Starting...")
    logger.info("=" * 80)
    
    # Log startup configuration (redacted secrets)
    logger.info(f"Configuration loaded:")
    logger.info(f"  - Search Endpoint: {config.search.endpoint}")
    logger.info(f"  - Search Index: {config.search.index_name}")
    logger.info(f"  - Embedding Deployment: {config.embedding.deployment}")
    logger.info(f"  - Embedding Dimensions: {config.embedding.dimensions}")
    logger.info(f"  - Log Level: {config.log_level}")
    logger.info(f"  - Log Format: {log_format}")
    logger.info(f"  - SSL Verify: {config.enable_ssl_verify}")
    logger.info(f"  - CORS Origins: {ALLOWED_ORIGINS}")
    
    # Initialize orchestrator
    rag_app = RAGOrchestrator(config)
    
    logger.info("API server initialized successfully")


@app.get("/")
async def root():
    """Root endpoint - basic health check"""
    return {"status": "healthy", "service": "SCORE AI Assistant API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """
    Health check endpoint for Azure App Service health probes.
    Returns detailed status of all dependencies.
    """
    global rag_app
    
    health_status = {
        "status": "healthy",
        "service": "SCORE AI Assistant API",
        "version": "1.0.0",
        "checks": {
            "rag_orchestrator": "ok" if rag_app else "not_initialized"
        }
    }
    
    # Check if RAG app is initialized
    if not rag_app:
        health_status["status"] = "degraded"
        health_status["checks"]["rag_orchestrator"] = "not_initialized"
    
    return health_status


# @app.post("/api/chat", response_model=ChatResponse)
# async def chat(request: ChatRequest):
#     """
#     Main chat endpoint
#     Processes user questions and returns AI-generated answers with sources
#     """
#     global rag_app, logger
    
#     if not rag_app:
#         raise HTTPException(status_code=503, detail="Service not initialized")
    
#     try:
#         logger.info(f"Chat request from {request.user_id}: {request.question[:50]}...")
        
#         # Process query
#         result = rag_app.process_query(
#             query=request.question,
#             session_id=request.conversation_id
#         )
        
#         return ChatResponse(
#             answer=result.get("answer", "Sorry, I couldn't process your request."),
#             type=result.get("type", "error"),
#             sources=result.get("sources", []),
#             top_sources_formatted=result.get("top_sources_formatted", "")  # ✅ ADD THIS LINE
#         )
        
#     except RAGException as e:
#         logger.error(f"RAG error: {str(e)}")
#         return ChatResponse(
#             answer="I encountered an error processing your question. Please try again.",
#             type="error",
#             error=str(e)
#         )
#     except Exception as e:
#         logger.error(f"Unexpected error: {str(e)}", exc_info=True)
#         raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint - processes user queries through RAG pipeline
    """
    if not rag_app:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        session_id = request.conversation_id or "default"
        logger.info(f"Chat request - Session: {session_id}, Query: {request.question[:50]}...")
        
        # ✅ Run sync process_query in thread pool (non-blocking)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,  # Use default thread pool
            lambda: rag_app.process_query(request.question, session_id)
        )
        
        return ChatResponse(
            answer=result.get("answer", "Sorry, I couldn't process your request."),
            type=result.get("type", "error"),
            sources=result.get("sources", []),
            top_sources_formatted=result.get("top_sources_formatted", "")
        )
        
    except RAGException as e:
        logger.error(f"RAG error: {str(e)}")
        return ChatResponse(
            answer="I encountered an error processing your question. Please try again.",
            type="error",
            sources=[],
            error=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/session/{session_id}/clear")
async def clear_session(session_id: str):
    """Clear a conversation session"""
    global rag_app, logger
    
    if not rag_app:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        rag_app.memory_service.clear_session(session_id)
        logger.info(f"Session cleared: {session_id}")
        return {"status": "success", "message": f"Session {session_id} cleared"}
    except Exception as e:
        logger.error(f"Error clearing session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear session")


@app.get("/api/session/{session_id}/stats", response_model=SessionStats)
async def get_session_stats(session_id: str):
    """Get session statistics"""
    global rag_app, logger
    
    if not rag_app:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        stats = rag_app.get_session_stats(session_id)
        return SessionStats(
            created_at=stats.get("created_at"),
            turn_count=stats.get("turn_count", 0)
        )
    except Exception as e:
        logger.error(f"Error getting session stats: {str(e)}")
        return SessionStats()


def main():
    """Run the FastAPI server (for local development only)"""
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disabled for production safety
        log_level="info"
    )


if __name__ == "__main__":
    main()
