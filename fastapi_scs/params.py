"""Query-parameter checks that cannot be expressed as per-parameter FastAPI validation."""

from fastapi import HTTPException, Request

from fastapi_scs.settings import get_settings

# Every parameter defined by the SCS 1.1 OpenAPI document. All of them are single-valued.
SCS_PARAMETERS = ("RA", "DEC", "SR", "MAXREC", "RESPONSEFORMAT", "VERB")


def check_query_params(request: Request) -> list[str]:
    """Reject repeated parameters and deal with unknown ones.

    - DALI: a service must respond with an error if a single-valued parameter is given more than once.
    - Unknown parameters: SCS 1.1 lets the service ignore them and report them in an
      INFO name="warning", whereas DALI-1.2 requires an error. See Settings.REJECT_UNKNOWN_PARAMS.

    Returns:
        The names of unknown parameters that were ignored, for reporting in the response.
    """
    names = [name for name, _ in request.query_params.multi_items()]

    repeated = sorted({name for name in names if name in SCS_PARAMETERS and names.count(name) > 1})
    if repeated:
        raise HTTPException(status_code=400, detail=f"Parameters must be single-valued: {', '.join(repeated)}")

    unknown = sorted({name for name in names if name not in SCS_PARAMETERS})
    if unknown and get_settings().REJECT_UNKNOWN_PARAMS:
        raise HTTPException(status_code=400, detail=f"Unknown parameters: {', '.join(unknown)}")

    return unknown
