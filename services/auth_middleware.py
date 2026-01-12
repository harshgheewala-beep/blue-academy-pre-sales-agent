import logging

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.requests import Request

logger = logging.getLogger("Middleware Logs")


class LogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(f"Processing request [{request.method}] : {request.url.path}")
        return await call_next(request)
