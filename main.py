import os
import uvicorn
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from logger import configure_logging
from routes.route_handler import all_routers
from utils.middleware import AuthMiddleware
from __init__ import __version__
from db_pool import Base, engine

load_dotenv()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="fastAPI",
        description="API and routes available in backend",
        version=__version__,
    )

    # Add Auth middleware (class-based)
    app.add_middleware(AuthMiddleware)

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include all routes
    all_routers(app)

    # Startup event
    @app.on_event("startup")
    def startup_event():
        logger = configure_logging(__name__)
        logger.info("Logger is configured.")
        
        # Create all tables
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created.")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            logger.warning("Continuing without database. Make sure PostgreSQL is running.")

        # Create data directory for attachment-worker service
        if os.getenv("SERVICE_TYPE") == "attachment-worker":
            os.makedirs("data", exist_ok=True)

    # Shutdown event
    @app.on_event("shutdown")
    def shutdown_event():
        logger = configure_logging(__name__)
        logger.info("Server is shutting down.")

    # Root endpoint
    @app.get("/")
    async def root():
        return {"message": "App API is running"}

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "ok"}

    # Favicon endpoint
    @app.get("/favicon.ico")
    async def favicon():
        pass

    return app


# Create FastAPI app
app = create_app()


def start_server(host: Optional[str] = None, port: Optional[int] = None):
    """Start the server."""
    uvicorn.run(
        "main:app",
        host=host or "0.0.0.0",
        port=port or 8000,
        reload=True,
        timeout_keep_alive=120,
        limit_concurrency=1000,
        limit_max_requests=10000,
        h11_max_incomplete_event_size=4194304,
    )


if __name__ == "__main__":
    start_server()
