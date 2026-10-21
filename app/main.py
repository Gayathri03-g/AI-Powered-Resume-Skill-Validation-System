"""
FastAPI Application Entry Point
CHUNK 1.1 - Clean server startup with health check
Frontend integration - Serves static HTML/CSS/JS
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core import settings
from app.api.v1.router import api_router
import os


def create_application() -> FastAPI:
    """
    Application factory
    Creates and configures FastAPI app
    """
    
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.API_DEBUG,
        docs_url="/docs" if settings.API_DEBUG else None,
        redoc_url="/redoc" if settings.API_DEBUG else None,
    )
    
    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API v1 router
    app.include_router(
        api_router,
        prefix="/api/v1"
    )
    
    # Get frontend directory path
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
    
    # Mount static files (CSS, JS, images)
    if os.path.exists(frontend_dir):
        app.mount("/css", StaticFiles(directory=os.path.join(frontend_dir, "css")), name="css")
        app.mount("/js", StaticFiles(directory=os.path.join(frontend_dir, "js")), name="js")
    
    # Root endpoint - Serve frontend
    @app.get("/")
    async def root():
        """Serve the frontend application"""
        index_path = os.path.join(frontend_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(
                index_path, 
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate", 
                    "Pragma": "no-cache", 
                    "Expires": "0"
                }
            )
        else:
            # Fallback API info
            return {
                "app": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "status": "running",
                "docs": "/docs" if settings.API_DEBUG else "disabled in production"
            }
    
    return app


# Create app instance
app = create_application()
