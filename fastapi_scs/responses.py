"""Response classes for FastAPI SCS"""

from fastapi import HTTPException
from fastapi.responses import Response

VOTABLE_MEDIA_TYPE = "application/x-votable+xml"

# RESPONSEFORMAT values this service accepts, mapped to the Content-Type returned.
# DALI: when a media type is requested, that exact media type must be echoed in Content-Type.
SUPPORTED_RESPONSEFORMATS = {
    "application/x-votable+xml": VOTABLE_MEDIA_TYPE,
    "text/xml": "text/xml",
    "votable": VOTABLE_MEDIA_TYPE,
}


class VOTableResponse(Response):
    """VOTable response class"""

    media_type = VOTABLE_MEDIA_TYPE


def resolve_response_format(responseformat: str | None) -> str:
    """Map a RESPONSEFORMAT value to the Content-Type to respond with.

    Unsupported formats are an error (SCS 1.1 sec. 2.2, DALI RESPONSEFORMAT).
    """
    if responseformat is None:
        return VOTABLE_MEDIA_TYPE
    try:
        return SUPPORTED_RESPONSEFORMATS[responseformat]
    except KeyError:
        supported = ", ".join(SUPPORTED_RESPONSEFORMATS)
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported RESPONSEFORMAT: {responseformat}. Supported values: {supported}",
        ) from None
