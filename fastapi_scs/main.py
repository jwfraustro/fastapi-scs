"""Main router for the Cone Search API."""

from fastapi import FastAPI

from fastapi_scs.router.conesearch_router import conesearch_router
from fastapi_scs.middleware import UppercaseQueryParamsMiddleware
from fastapi_scs.exceptions import general_exception_handler, http_exception_handler, validation_exception_handler
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException

app = FastAPI(title="Simple Cone Search API",
              description="A simple API for performing cone searches on astronomical data.",
             version="1.0.0")

# Middleware to convert all query parameter names to uppercase
app.add_middleware(UppercaseQueryParamsMiddleware)

# Exception handlers
app.add_exception_handler(Exception, general_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Include the Cone Search router
app.include_router(conesearch_router)