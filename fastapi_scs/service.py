"""Service module for Simple Cone Search in FastAPI.

Implementors should extend this module to define their own service logic: the column metadata
in COLUMNS and the query in perform_conesearch are stand-ins for a real catalogue.
"""

import io
from dataclasses import dataclass
from datetime import datetime, timezone

from astropy.io.votable import tree
from fastapi.responses import Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from fastapi_scs.responses import VOTableResponse

VOTABLE_VERSION = "1.4"
SCS_STANDARD_ID = "ivo://ivoa.net/std/ConeSearch"


@dataclass(frozen=True)
class Column:
    """Metadata for one output column.

    `verb` is the lowest VERB level at which the column is returned.
    """

    name: str
    datatype: str
    ucd: str
    description: str
    verb: int = 1
    unit: str | None = None
    arraysize: str | None = None


# SCS 1.1 requires exactly one FIELD each with ucd meta.id;meta.main (char array),
# pos.eq.ra;meta.main and pos.eq.dec;meta.main (float or double, decimal degrees).
COLUMNS = [
    Column("name", "char", "meta.id;meta.main", "Source identifier", verb=1, arraysize="*"),
    Column("ra", "double", "pos.eq.ra;meta.main", "Right ascension (ICRS)", verb=1, unit="deg"),
    Column("dec", "double", "pos.eq.dec;meta.main", "Declination (ICRS)", verb=1, unit="deg"),
    Column("flux", "double", "phot.flux", "Source flux (arbitrary units)", verb=2),
    Column("id", "long", "meta.record", "Internal row number", verb=3),
]


def columns_for_verb(verb: int) -> list[Column]:
    """Columns returned for a given VERB level (1 = minimal, 2 = typical, 3 = everything)."""
    return [column for column in COLUMNS if column.verb <= verb]


def _info(name: str, value: str, content: str | None = None) -> tree.Info:
    info = tree.Info(name=name, value=value)
    if content:
        info.content = content
    return info


def generate_votable(
    columns: list[Column],
    rows: list[dict],
    *,
    overflow: bool,
    request_url: str,
    ignored_params: list[str],
    media_type: str,
) -> Response:
    """Generate a DALI-compliant VOTable for the cone search results.

    The table is built from the column metadata rather than from the rows, so that empty
    results, SR=0 and MAXREC=0 still return the full FIELD description.
    """
    votable = tree.VOTableFile(version=VOTABLE_VERSION)
    resource = tree.Resource(type="results")
    votable.resources.append(resource)

    # DALI: the results RESOURCE must carry a QUERY_STATUS INFO before the TABLE. When the output
    # was truncated, the initial QUERY_STATUS may itself be OVERFLOW.
    if overflow:
        resource.infos.append(_info("QUERY_STATUS", "OVERFLOW", "Result truncated at MAXREC"))
    else:
        resource.infos.append(_info("QUERY_STATUS", "OK", "Successful query"))
    resource.infos.append(_info("standardID", SCS_STANDARD_ID))
    resource.infos.append(_info("request", request_url))
    resource.infos.append(_info("request_date", datetime.now(timezone.utc).isoformat()))
    if ignored_params:
        # SCS 1.1 sec. 2.1: report ignored optional/custom parameters as a warning.
        resource.infos.append(
            _info("warning", f"Unrecognized optional/custom parameters. Ignored: {', '.join(ignored_params)}")
        )

    table = tree.TableElement(votable)
    resource.tables.append(table)
    for column in columns:
        field = tree.Field(
            votable,
            name=column.name,
            datatype=column.datatype,
            arraysize=column.arraysize,
            ucd=column.ucd,
            unit=column.unit,
        )
        field.description = column.description
        table.fields.append(field)

    table.create_arrays(len(rows))
    for i, row in enumerate(rows):
        values = [row[column.name] for column in columns]
        table.array[i] = tuple(_fill_value(column) if value is None else value for column, value in zip(columns, values))
        table.array.mask[i] = tuple(value is None for value in values)

    buffer = io.BytesIO()
    votable.to_xml(buffer)

    return VOTableResponse(content=buffer.getvalue(), media_type=media_type)


def _fill_value(column: Column):
    """Placeholder stored under a mask for NULL values."""
    if column.datatype == "char":
        return ""
    return 0


def perform_conesearch(  # pylint: disable=too-many-arguments
    session: Session,
    ra: float,
    dec: float,
    sr: float,
    maxrec: int,
    verb: int,
) -> tuple[list[Column], list[dict], bool]:
    """
    Perform a cone search based on the provided coordinates and radius.

    Args:
        session: Database session.
        ra (float): Right Ascension in decimal degrees.
        dec (float): Declination in decimal degrees.
        sr (float): Search radius in decimal degrees.
        maxrec (int): Maximum number of records to return.
        verb (int): Verbosity level (1, 2, or 3).

    Returns:
        The columns to report, the result rows, and whether the result was truncated.
    """
    columns = columns_for_verb(verb)

    # SR=0 (SCS 1.1) and MAXREC=0 (DALI) are metadata queries: no need to touch the database.
    if sr == 0 or maxrec == 0:
        return columns, [], False

    # Example conesearch with postgres & pgsphere. One extra row is fetched to detect overflow.
    column_list = ", ".join(column.name for column in columns)
    query = text(f"""
                 SELECT {column_list} FROM sources
                 WHERE coord @ scircle(spoint(:ra, :dec), :sr)
                 LIMIT :limit;
                 """)  # nosec B608 - column names come from COLUMNS, not from the request
    result = session.execute(query, {"ra": ra, "dec": dec, "sr": sr, "limit": maxrec + 1})
    rows = [dict(row) for row in result.mappings().all()]

    overflow = len(rows) > maxrec
    return columns, rows[:maxrec], overflow
