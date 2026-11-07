"""Main API router for the Cone Search service (SCS 1.1)."""

from fastapi import APIRouter, Depends, Query, Request
from fastapi_restful.cbv import cbv
from sqlalchemy.orm import Session

from fastapi_scs.dependencies import get_session
from fastapi_scs.params import check_query_params
from fastapi_scs.responses import VOTABLE_MEDIA_TYPE, VOTableResponse, resolve_response_format
from fastapi_scs.service import generate_votable, perform_conesearch
from fastapi_scs.settings import get_settings

settings = get_settings()

conesearch_router = APIRouter()

SEARCH_RESPONSES = {
    200: {
        "description": (
            "Successful query, returns a table containing the astronomical sources whose positions "
            "are within the cone described by RA, DEC, SR"
        ),
        "content": {VOTABLE_MEDIA_TYPE: {}, "text/xml": {}},
    },
    400: {
        "description": "invalid request/input",
        "content": {"text/plain": {"schema": {"type": "string"}}},
    },
}


@cbv(conesearch_router)
class ConeSearchRouter:
    """Router for Cone Search API endpoints."""

    @conesearch_router.get(
        "/search",
        operation_id="search",
        summary="The Simple Cone Search base query endpoint",
        description=(
            "Parametric HTTP GET queries following ConeSearch to retrieve astrophysics sources within the cone"
        ),
        response_class=VOTableResponse,
        responses=SEARCH_RESPONSES,
    )
    def search(  # pylint: disable=too-many-arguments
        self,
        request: Request,
        ra: float = Query(
            ...,
            alias="RA",
            ge=0.0,
            le=360.0,
            example=180.0,
            description="Right ascension (ICRS) of the centre of the cone, in decimal degrees",
        ),
        dec: float = Query(
            ...,
            alias="DEC",
            ge=-90.0,
            le=90.0,
            example=0.0,
            description="Declination (ICRS) of the centre of the cone, in decimal degrees",
        ),
        sr: float = Query(
            ...,
            alias="SR",
            ge=0.0,
            example=1,
            le=settings.MAX_SR,
            description=(
                "Radius of the cone, in decimal degrees. SR=0 returns only the metadata of the response, "
                "like MAXREC=0."
            ),
        ),
        # MAXREC and RESPONSEFORMAT default to None but are annotated without "| None" so the generated
        # OpenAPI shows a plain integer/string schema like the DALI components, not anyOf [..., null].
        maxrec: int = Query(
            None,
            alias="MAXREC",
            ge=0,
            description="Maximum number of records to return; MAXREC=0 requests only the response metadata",
        ),
        responseformat: str = Query(
            None,
            alias="RESPONSEFORMAT",
            description="Output format: application/x-votable+xml (default), text/xml or votable",
        ),
        verb: int = Query(
            2,
            alias="VERB",
            ge=1,
            le=3,
            description="Verbosity: 1 = minimal columns, 2 = typical columns (default), 3 = all columns",
        ),
        ignored_params: list[str] = Depends(check_query_params),
        session: Session = Depends(get_session),
    ):
        """
        Perform a Cone Search.

        Returns:
            VOTable response with the query results.
        """
        media_type = resolve_response_format(responseformat)

        # DALI MAXREC: apply a default when absent and never exceed the service's hard limit.
        effective_maxrec = min(settings.DEFAULT_MAXREC if maxrec is None else maxrec, settings.MAX_MAXREC)

        columns, rows, overflow = perform_conesearch(session, ra, dec, sr, effective_maxrec, verb)

        return generate_votable(
            columns,
            rows,
            overflow=overflow,
            request_url=str(request.url),
            ignored_params=ignored_params,
            media_type=media_type,
        )
