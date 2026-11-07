"""Exceptions for FastAPI SCS.

SCS 1.1 defers error documents to DALI, and the SCS 1.1 OpenAPI document references the VOSI
standard `bad-request` response, which is text/plain. DALI-1.2 also strongly recommends text/plain
error documents, so every error here is a plain-text body with an appropriate HTTP status code.
"""

from fastapi.responses import PlainTextResponse


def error_response(message: str, status_code: int) -> PlainTextResponse:
    """Create a plain-text DALI error response."""
    return PlainTextResponse(content=message + "\n", status_code=status_code)


async def general_exception_handler(request, exc) -> PlainTextResponse:  # pylint: disable=unused-argument
    """
    General exception handler for unhandled exceptions.
    """
    return error_response("An unexpected error occurred. Please try again later.", 500)


async def http_exception_handler(request, exc) -> PlainTextResponse:  # pylint: disable=unused-argument
    """StarletteHTTPException handler"""
    return error_response(str(exc.detail).replace("\n", " ").strip(), exc.status_code)


async def validation_exception_handler(request, exc) -> PlainTextResponse:  # pylint: disable=unused-argument
    """Exception handler for request validation errors (missing, unparseable or out-of-range parameters)."""
    messages = []
    for error in exc.errors():
        param = error["loc"][-1] if error["loc"] else "request"
        messages.append(f"Invalid value for parameter {param}: {error['msg']}")
    return error_response("; ".join(messages), 400)
