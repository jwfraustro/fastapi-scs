"""Main application for the Cone Search API."""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException

from fastapi_scs.exceptions import general_exception_handler, http_exception_handler, validation_exception_handler
from fastapi_scs.middleware import UppercaseQueryParamsMiddleware
from fastapi_scs.router.conesearch_router import conesearch_router
from fastapi_scs.settings import get_settings

settings = get_settings()

app = FastAPI(
    title="IVOA Simple Cone Search",
    description="A simple API for performing cone searches on astronomical data, following ConeSearch-1.1.",
    root_path=settings.ROOT_PATH,
    version="1.1",
)

if settings.CASE_INSENSITIVE_PARAMS:
    # Legacy (SCS 1.0 / pre-DALI-1.2) behaviour: accept parameter names in any case.
    app.add_middleware(UppercaseQueryParamsMiddleware)

# Exception handlers: all errors are text/plain documents (DALI, VOSI bad-request)
app.add_exception_handler(Exception, general_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Tags are set here rather than on the APIRouter, where fastapi_restful.cbv would duplicate them
app.include_router(conesearch_router, tags=["SCS"])


_default_openapi = app.openapi


def scs_openapi() -> dict:
    """OpenAPI document for the service, without FastAPI's automatic 422 responses.

    Validation errors are returned as 400 text/plain (see exceptions.py), as the SCS 1.1 document specifies.
    """
    if app.openapi_schema:
        return app.openapi_schema
    schema = _default_openapi()
    for path_item in schema.get("paths", {}).values():
        for operation in path_item.values():
            operation.get("responses", {}).pop("422", None)
    component_schemas = schema.get("components", {}).get("schemas", {})
    for name in ("HTTPValidationError", "ValidationError"):
        component_schemas.pop(name, None)
    if "components" in schema and not component_schemas:
        schema["components"].pop("schemas", None)
        if not schema["components"]:
            schema.pop("components")
    return schema


app.openapi = scs_openapi
