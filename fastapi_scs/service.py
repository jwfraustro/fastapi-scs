"""Service module for Simple Cone Search in FastAPI.

Implementors should extend this module to define their own service logic.
"""

import io

from astropy.io.votable import from_table, writeto
from astropy.io.votable.tree import VOTableFile
from astropy.table import Table
from fastapi.responses import Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from fastapi_scs.responses import XMLResponse


def generate_votable(rows: list[dict]) -> Response:
    """Generate a basic VOTable for the conesearch results."""

    table = Table(rows)
    votable: VOTableFile = from_table(table)

    for field in votable.get_first_table().fields:
        if field.ID == "ra":
            field.ucd = "POS_EQ_RA_MAIN"
            field.datatype = "double"
        elif field.ID == "dec":
            field.ucd = "POS_EQ_DEC_MAIN"
            field.datatype = "double"
        elif field.ID == "name":
            field.ucd = "ID_MAIN"
            field.datatype = "char"
        elif field.ID == "flux":
            field.ucd = "phot.flux"
            field.datatype = "double"

    buffer = io.BytesIO()
    writeto(votable, buffer)
    buffer.seek(0)

    return XMLResponse(content=buffer.read())


def perform_conesearch(session: Session, ra: float, dec: float, sr: float, verb: int):
    """
    Perform a cone search based on the provided coordinates and radius.

    Args:
        ra (float): Right Ascension in degrees.
        dec (float): Declination in degrees.
        sr (float): Search radius in arcseconds.
        verb (int): Verbosity level (1, 2, or 3).

    Returns:
        dict: Search results.
    """
    # Example conesearch with postgres

    query = text("""
                 SELECT * FROM sources
                 WHERE q3c_radial_query(ra, dec, :ra, :dec, :sr)
                 """)
    result = session.execute(query, {"ra": ra, "dec": dec, "sr": sr})
    rows = result.mappings().all()

    votable_response = generate_votable(rows)

    return votable_response
