"""Main API router for the Cone Search service."""
from fastapi import APIRouter, Path, Query
from fastapi_restful.cbv import cbv
from fastapi import Depends
from fastapi_scs.service import perform_conesearch
from sqlalchemy.orm import Session
from fastapi_scs.dependencies import get_session

conesearch_router = APIRouter(tags=["SCS"])


@cbv(conesearch_router)
class ConeSearchRouter:
    """Router for Cone Search API endpoints."""

    @conesearch_router.get(
        "/conesearch",
        summary="Perform a Cone Search",
        description="Perform a Cone Search based on the provided coordinates and radius.",
    )
    def conesearch(
        self,
        ra: float = Query(..., description="Right Ascension in degrees", ge=0., le=360., alias="RA"),
        dec: float = Query(..., description="Declination in degrees", ge=-90., le=90., alias="DEC"),
        sr: float = Query(..., description="Search radius in arcseconds", alias="SR"),
        verb: int = Query(1, description="Verbosity level", ge=1, le=3, alias="VERB"),
        session: Session = Depends(get_session)
    ):
        """
        Perform a Cone Search.

        Args:
            ra (float): Right Ascension in degrees.
            dec (float): Declination in degrees.
            sr (float): Search radius in arcseconds.
            verb (int): Verbosity level (1, 2, or 3).

        Returns:
            JSON response with search results.
        """

        # Placeholder for actual search logic
        return perform_conesearch(session, ra, dec, sr, verb)