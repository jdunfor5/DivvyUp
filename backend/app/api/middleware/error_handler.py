from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.base import BaseHTTPMiddleware

from app.dependencies.logging import get_logger

logger = get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except SQLAlchemyError as e:
            logger.warning("Database error on %s %s: %s", request.method, request.url.path, e)
            return JSONResponse(
                status_code=500,
                content={"detail": "An error occurred"},
            )
        except Exception as e:
            logger.error("Unhandled exception on %s %s: %s", request.method, request.url.path, e, exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"detail": "An internal server error occurred"},
            )
