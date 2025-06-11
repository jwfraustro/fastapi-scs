"""
VO Simple Cone Search API
"""

from asb.core import service_fastapi as service
from fastapi import APIRouter, Depends, Query, Request
from fastapi.datastructures import QueryParams
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import Response, StreamingResponse
from fastapi_restful.cbv import cbv
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ASGIApp, Receive, Scope, Send

from mast.vo_conesearch.services.search_context import SearchContext

service_name = "cone_search"
router = APIRouter()


class XMLResponse(Response):
    """votable response class"""

    media_type = "text/xml"


@cbv(router)
class ConeSearchHandler(service.BaseHandler):
    """Simple Cone Search Handler"""

    # pylint: disable=invalid-name, unused-argument

    @router.get("/{catalog}", response_class=StreamingResponse)
    def get(
        self,
        # This Depends() is where the 'catalog' value is used to get the catalog-specific
        # values such as DB 'cnxn' and 'max_radius', which are then available through 'context'.
        context: SearchContext = Depends(SearchContext.yield_context),
        ra: float = Query(
            ...,
            ge=0,
            le=360,
            description="right-ascension in the ICRS coordinate system for the positon of the center of the cone to "
            "search, given in decimal degrees",
        ),
        dec: float = Query(
            ...,
            ge=-90,
            le=90,
            description="declination in the ICRS coordinate system for the positon of the center of the cone to "
            "search, given in decimal degrees",
        ),
        sr: float = Query(
            ...,
            ge=0,
            le=180,  # search radius on spec is up to 180.  Real limit is catalog-specific.
            description="the radius of the cone to search, given in decimal degrees",
        ),
        verb: int = Query(
            2,
            ge=1,
            le=3,
            description="either 1, 2, or 3-indicating verbosity which determines how "
            "many columns are to be returned in the resulting table",
        ),
        # Accept all the common API args.  For now, only 'format' will be used.
        commons: dict = Depends(service.common_db_args),
    ):
        """Simple cone search"""
        result = self.do_query(context, ra, dec, sr, verb, commons)

        return result

    def do_query(self, context, ra, dec, sr, verb, commons):
        """
        Perform the query for the specified arguments.  Of all the commons arguments, only *format*
        will be used.
        """

        # todo: Log this query

        max_radius = context.catalog_info["max_radius"]
        if sr > max_radius:
            raise StarletteHTTPException(
                status_code=400, detail=f"SR value {sr} exceeds maximum allowable for catalog ({max_radius})."
            )

        query = context.catalog_info["query"]
        query_args = [ra, dec, sr]

        # asb.core result streaming picks up this metadata for VOTable headers
        self.metadata_json = context.catalog_metadata
        self.nested_format = True

        # we make the call to db_result with all our args
        stream, content_type = self.db_result(context.cnxn, query, query_args=query_args, **commons)

        # return the database result as a streaming response
        return StreamingResponse(stream, media_type=content_type)


service.add_argument("--db", type=str, required=True, help="db config file")
service.add_argument("--catalog_configs", type=str, required=True, help="Catalog configurations file")

app = service.app(service_name)
app.include_router(router)


class LowerCaseParamsMiddleware:
    """
    Middleware to make all params lowercase. This allows us to accept both lower and uppercase versions of
    the params.

    e.g, a request:
        /tic?RA=1&DEC=2&sr=.01&format=votable
    will be transformed into:
        /tic?ra=1&dec=2&sr=.01&format=votable

    """

    # pylint: disable=redefined-outer-name
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            request = Request(scope=scope)
            query_params = request.query_params

            params_lower = {k.lower(): v for k, v in query_params.items()}
            query_params_update = QueryParams(params_lower)

            # only scope/state are carried through
            request.scope["query_string"] = bytes(str(query_params_update), "ascii")

        await self.app(scope, receive, send)


VOTABLE_ERROR_XML = """<?xml version="1.0" encoding="UTF-8"?>
<VOTABLE version="1.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xmlns="http://www.ivoa.net/xml/VOTable/v1.1"
  xsi:schemaLocation="http://www.ivoa.net/xml/VOTable/v1.1 http://www.ivoa.net/xml/VOTable/v1.1">
  <DESCRIPTION>MAST Simple Cone Search Service</DESCRIPTION>
  <INFO ID="Error" name="Error" value="{error}"/>
</VOTABLE>"""


# Error handlers


def votable_error_response(message, status_code):
    """
    From: https://www.ivoa.net/documents/REC/DAL/ConeSearch-20080222.html
    Error INFO as child of VOTABLE (preferred)
    """
    response = XMLResponse(content=VOTABLE_ERROR_XML.format(error=message), status_code=status_code)
    return response


async def general_exception_handler(request, exc) -> XMLResponse:  # pylint: disable=unused-argument
    """
    Generic exception handler for any exceptions not caught elsewhere.

    Uses a generic error string instead of including more detailed info that may have come with the exception.
    """

    # this handler catches our exceptions & prevents core from logging exceptions, so we need to do it
    request.state.log.exception(f"Request failed with exception, 500 {service.request_summary(request)}", exc_info=exc)

    # if it's not an HTTPException, return a generic error message, and throw a 500
    error_str = "An error occurred in processing the request"
    return votable_error_response(error_str, 500)


# pylint: disable=unused-argument
async def http_exception_handler(request, exc):
    """Exception handler for StarletteHTTPExceptions"""

    # http exceptions have a detail attribute which we can substitute in the error field
    error_str = exc.detail.replace("\n", " ").strip()
    return votable_error_response(error_str, exc.status_code)


async def validation_exception_handler(request, exc) -> XMLResponse:  # pylint: disable=unused-argument
    """Exception handler for validation errors"""

    errors = exc.errors()
    error_str = ", ".join([f"Error in {e['loc'][0]} {e['loc'][1]}: {e['msg']}" for e in errors])
    return votable_error_response(error_str, 400)


# App initialization
# todo:  Look into making this prettier by possibly
#        - not needing to remember to add lines below for any new handlers
#        - avoiding unnecessary app creation whenever this module is imported or loaded
#        - making search_context and other request-specific info available to error handlers
#          (not strictly needed since the request object is available, but interesting anyway)
def init_app(created_app):
    """
    This function performs any additional initialization needed for the FastAPI app created with
    either asb.core.service_fastapi.app() inline in this file (executed implicitly by
    asb.core.service_fastapi.bind("mast.vo_conesearch.services.api:app")),
    or asb.core.test.util_fastapi.TestServiceBase.create_app() for testing.
    """
    created_app.add_exception_handler(Exception, general_exception_handler)
    created_app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    created_app.add_exception_handler(RequestValidationError, validation_exception_handler)
    created_app.add_middleware(LowerCaseParamsMiddleware)
    created_app.add_middleware(GZipMiddleware)


init_app(app)


def make_doc_router():
    """part of doc autogen"""
    return router


if __name__ == "__main__":
    service.bind("mast.vo_conesearch.services.api:app")
