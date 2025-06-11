"""Middleware for the Simple Cone Search API."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.datastructures import QueryParams
from starlette.types import ASGIApp
from urllib.parse import urlencode


class UppercaseQueryParamsMiddleware(BaseHTTPMiddleware):
    """Middleware to convert all query parameter names to uppercase.

    The DALI spec requires that query parameter names are case-insensitive,
    and this middleware ensures that all query parameter names are converted to uppercase for consistency.
    """
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        # Convert query parameter names to uppercase
        original_query = request.query_params.multi_items()
        upper_query = [(key.upper(), value) for key, value in original_query]

        # Replace the scope's query string with the normalized version
        new_query_string = urlencode(upper_query, doseq=True)
        request.scope["query_string"] = new_query_string.encode("utf-8")

        return await call_next(request)
