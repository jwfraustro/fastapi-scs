"""Exceptions for FastAPI SCS."""

from fastapi.responses import Response

from fastapi_scs.responses import XMLResponse

# A boilerplate VOTable error response
VOTABLE_ERROR_XML = """<?xml version="1.0" encoding="UTF-8"?>
<VOTABLE version="1.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xmlns="http://www.ivoa.net/xml/VOTable/v1.1"
  xsi:schemaLocation="http://www.ivoa.net/xml/VOTable/v1.1 http://www.ivoa.net/xml/VOTable/v1.1">
  <DESCRIPTION>MAST Simple Cone Search Service</DESCRIPTION>
  <INFO ID="Error" name="Error" value="{error}"/>
</VOTABLE>"""

# Error handlers


def votable_error_response(message: str, status_code: int) -> Response:
    """Create a VOTable error response.

    INFO element containing the error as preferred by https://www.ivoa.net/documents/REC/DAL/ConeSearch-20080222.html
    """
    xml_response = XMLResponse(content=VOTABLE_ERROR_XML.format(error=message), status_code=status_code)
    return xml_response

async def general_exception_handler(request, exc) -> XMLResponse:  # pylint: disable=unused-argument
    """
    General exception handler for unhandled exceptions.
    """

    # Throw a generic error message
    error_str = "An unexpected error occurred. Please try again later."
    return votable_error_response(error_str, 500)


async def http_exception_handler(request, exc):
    """StarletteHTTPException handler"""

    error_str = exc.detail.replace("\n", " ").strip()
    return votable_error_response(error_str, exc.status_code)


async def validation_exception_handler(request, exc) -> XMLResponse:  # pylint: disable=unused-argument
    """Exception handler for request validation errors."""

    errors = exc.errors()
    error_str = ", ".join([f"Error in {e['loc'][0]} {e['loc'][1]}: {e['msg']}" for e in errors])
    return votable_error_response(error_str, 400)
