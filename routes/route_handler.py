from fastapi import FastAPI
from routes.intent_routes import intent_router


def all_routers(app: FastAPI):
    """Include all routers in the FastAPI app."""
    app.include_router(intent_router)