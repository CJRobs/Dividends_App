"""
Error Logging Middleware.

Captures and logs all unhandled exceptions for debugging.
"""

import logging
import traceback
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime

logger = logging.getLogger(__name__)


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all unhandled exceptions with full traceback.

    Logs errors to both console and file for easy debugging.
    """

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            # Log the full exception with traceback
            error_id = datetime.now().strftime("%Y%m%d-%H%M%S-%f")

            logger.error(
                f"Unhandled exception [{error_id}] on {request.method} {request.url.path}",
                exc_info=True,
                extra={
                    "error_id": error_id,
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": str(request.query_params),
                    "client": request.client.host if request.client else None,
                }
            )

            # Write detailed error to file
            error_file = f"logs/error_{error_id}.txt"
            try:
                import os
                os.makedirs("logs", exist_ok=True)
                with open(error_file, 'w') as f:
                    f.write(f"Error ID: {error_id}\n")
                    f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                    f.write(f"Method: {request.method}\n")
                    f.write(f"Path: {request.url.path}\n")
                    f.write(f"Query Params: {request.query_params}\n")
                    f.write(f"Headers: {dict(request.headers)}\n")
                    f.write(f"\n{'='*80}\n\n")
                    f.write(f"Exception Type: {type(exc).__name__}\n")
                    f.write(f"Exception Message: {str(exc)}\n\n")
                    f.write("Traceback:\n")
                    f.write(traceback.format_exc())

                logger.info(f"Error details saved to: {error_file}")
            except Exception as file_error:
                logger.error(f"Failed to write error file: {file_error}")

            # Return JSON error response
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal server error",
                    "error_id": error_id,
                    "message": str(exc) if logger.level == logging.DEBUG else "An error occurred",
                    "detail": f"Error logged with ID: {error_id}"
                }
            )
