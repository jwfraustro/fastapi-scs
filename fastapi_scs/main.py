"""Main application for the Cone Search API.

The SCS 1.1 OpenAPI document declares `servers: [{url: /cone}]` with a single `/search` path, so the
SCS application is a sub-application mounted at Settings.SCS_BASE_PATH. Its own OpenAPI document
(e.g. /cone/openapi.json) then has the same shape as the standard's.
"""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException

from fastapi_scs.exceptions import general_exception_handler, http_exception_handler, validation_exception_handler
from fastapi_scs.middleware import UppercaseQueryParamsMiddleware
from fastapi_scs.router.conesearch_router import conesearch_router
from fastapi_scs.settings import get_settings

settings = get_settings()

scs_app = FastAPI(
    title="IVOA Simple Cone Search",
    description="A simple API for performing cone searches on astronomical data, following ConeSearch-1.1.",
    version="1.1",
)

# Exception handlers: all errors are text/plain documents (DALI, VOSI bad-request)
scs_app.add_exception_handler(Exception, general_exception_handler)
scs_app.add_exception_handler(HTTPException, http_exception_handler)
scs_app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Tags are set here rather than on the APIRouter, where fastapi_restful.cbv would duplicate them
scs_app.include_router(conesearch_router, tags=["SCS"])


_default_openapi = scs_app.openapi


def scs_openapi() -> dict:
    """OpenAPI document for the SCS application, without FastAPI's automatic 422 responses.

    Validation errors are returned as 400 text/plain (see exceptions.py), as the SCS 1.1 document specifies.
    """
    if scs_app.openapi_schema:
        return scs_app.openapi_schema
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


scs_app.openapi = scs_openapi


app = FastAPI(
    title="Simple Cone Search API",
    root_path=settings.ROOT_PATH,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

if settings.CASE_INSENSITIVE_PARAMS:
    # Legacy (SCS 1.0 / pre-DALI-1.2) behaviour: accept parameter names in any case.
    app.add_middleware(UppercaseQueryParamsMiddleware)

app.mount(settings.SCS_BASE_PATH, scs_app)
