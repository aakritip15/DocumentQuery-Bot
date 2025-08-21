from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import routes

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    app = FastAPI(title="Document Q&A API", version="1.0.0")
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure this properly for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(routes.router, prefix="/api/v1", tags=["api"])
    
    return app