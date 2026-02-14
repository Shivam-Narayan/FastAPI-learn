from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
import json
from logger import configure_logging

logger = configure_logging(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Parse filters from query parameters if present
        filters_param = request.query_params.get("filters")
        if filters_param:
            try:
                request.state.filters = json.loads(filters_param)
            except json.JSONDecodeError:
                request.state.filters = None
        else:
            request.state.filters = None
        
        response = await call_next(request)
        return response
