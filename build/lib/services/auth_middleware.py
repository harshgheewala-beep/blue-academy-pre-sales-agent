import logging

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.requests import Request
from fastapi import HTTPException
from services.authentication import get_current_user
from logging import Logger

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Auth Middleware")


class AuthMiddleware(BaseHTTPMiddleware):
    # async def __call__(self, request: Request, call_next):
    #     pass

    async def dispatch(self, request: Request, call_next):
        logger.info(f"Processing request {request.url.path}")
        if request.url.path in ["/users/login","/docs","/openapi.json"]:
            return await call_next(request)


        # try:
        #     return await call_next(request)
        #
        #     user_payload = get_current_user(request)
        #     request.state.user = user_payload
        #
        # except Exception as e:
        #     # logger.error(e)
        #     raise HTTPException(status_code=401,
        #                             detail="Unauthorized Access")

        return await call_next(request)
