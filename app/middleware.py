import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from .logger import logger

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        process_time = time.time() - start

        logger.info(
            {
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time_ms": int(process_time * 1000)
            }
        )
        return response
