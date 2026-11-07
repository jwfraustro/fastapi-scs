"""Tests for the SCS 1.1 endpoint."""

import io

import pytest
from astropy.io.votable import parse

from fastapi_scs.settings import get_settings

SEARCH = "/search"
VALID = "RA=10&DEC=20&SR=0.05"


def votable(response):
    """Parse a response body as a VOTable."""
    return parse(io.BytesIO(response.content))


def results_resource(response):
    """The RESOURCE type="results" of a VOTable response."""
    resources = [r for r in votable(response).resources if r.type == "results"]
    assert len(resources) == 1
    return resources[0]


def infos(response):
    """INFO name -> value in the results resource."""
    return {info.name: info.value for info in results_resource(response).infos}


def ucds(response):
    """UCDs of the FIELDs in the results table."""
    return [field.ucd for field in results_resource(response).tables[0].fields]


# --- Successful responses -------------------------------------------------------------------------


def test_search_endpoint_path(client):
    """The query endpoint is /search relative to the service's base URL."""
    assert client.get(f"{SEARCH}?{VALID}").status_code == 200
    assert client.get(f"/conesearch?{VALID}").status_code == 404


def test_default_content_type_is_votable(client):
    """application/x-votable+xml is the default media type."""
    response = client.get(f"{SEARCH}?{VALID}")
    assert response.headers["content-type"].startswith("application/x-votable+xml")


def test_required_fields_and_query_status(client):
    """The response carries QUERY_STATUS=OK and exactly one each of the three mandatory UCDs."""
    response = client.get(f"{SEARCH}?{VALID}")
    assert infos(response)["QUERY_STATUS"] == "OK"
    field_ucds = ucds(response)
    for ucd in ("meta.id;meta.main", "pos.eq.ra;meta.main", "pos.eq.dec;meta.main"):
        assert field_ucds.count(ucd) == 1
    fields = {f.ucd: f for f in results_resource(response).tables[0].fields}
    assert fields["meta.id;meta.main"].datatype == "char"
    assert fields["meta.id;meta.main"].arraysize == "*"
    assert fields["pos.eq.ra;meta.main"].unit == "deg"
    assert fields["pos.eq.dec;meta.main"].unit == "deg"


@pytest.mark.parametrize("query", ["RA=10&DEC=20&SR=0", f"{VALID}&MAXREC=0"])
def test_metadata_queries(client, fake_session, query):
    """SR=0 and MAXREC=0 return the full FIELD metadata with no rows, without querying the database."""
    response = client.get(f"{SEARCH}?{query}")
    assert response.status_code == 200
    assert infos(response)["QUERY_STATUS"] == "OK"
    assert "pos.eq.ra;meta.main" in ucds(response)
    assert len(results_resource(response).tables[0].array) == 0
    assert fake_session.calls == []


def test_maxrec_overflow(client, fake_session):
    """When the result exceeds MAXREC, rows are truncated and QUERY_STATUS is OVERFLOW."""
    response = client.get(f"{SEARCH}?{VALID}&MAXREC=2")
    assert infos(response)["QUERY_STATUS"] == "OVERFLOW"
    assert len(results_resource(response).tables[0].array) == 2
    assert fake_session.calls[0][1]["limit"] == 3


def test_maxrec_not_reached(client):
    """When the result fits in MAXREC, QUERY_STATUS stays OK."""
    response = client.get(f"{SEARCH}?{VALID}&MAXREC=10")
    assert infos(response)["QUERY_STATUS"] == "OK"
    assert len(results_resource(response).tables[0].array) == 5


def test_maxrec_hard_limit(client, fake_session):
    """MAXREC larger than the service limit is capped, and the default applies when absent."""
    settings = get_settings()
    client.get(f"{SEARCH}?{VALID}&MAXREC={settings.MAX_MAXREC * 10}")
    client.get(f"{SEARCH}?{VALID}")
    assert fake_session.calls[0][1]["limit"] == settings.MAX_MAXREC + 1
    assert fake_session.calls[1][1]["limit"] == settings.DEFAULT_MAXREC + 1


@pytest.mark.parametrize(
    "responseformat, content_type",
    [
        ("application/x-votable+xml", "application/x-votable+xml"),
        ("votable", "application/x-votable+xml"),
        ("text/xml", "text/xml"),
    ],
)
def test_supported_responseformats(client, responseformat, content_type):
    """Supported RESPONSEFORMAT values; a requested media type is echoed in Content-Type."""
    response = client.get(SEARCH, params={"RA": 10, "DEC": 20, "SR": 0.05, "RESPONSEFORMAT": responseformat})
    assert response.status_code == 200
    assert response.headers["content-type"].split(";")[0] == content_type


@pytest.mark.parametrize("verb, expected", [(1, 3), (2, 4), (3, 5), (None, 4)])
def test_verb(client, verb, expected):
    """VERB selects the number of columns and defaults to 2."""
    query = VALID if verb is None else f"{VALID}&VERB={verb}"
    response = client.get(f"{SEARCH}?{query}")
    assert len(results_resource(response).tables[0].fields) == expected


def test_unknown_parameters_warn(client):
    """By default (SCS 1.1), unknown parameters are ignored and reported in an INFO name="warning"."""
    response = client.get(f"{SEARCH}?{VALID}&FOO=1&BAR=2")
    assert response.status_code == 200
    assert infos(response)["warning"].endswith("Ignored: BAR, FOO")


def test_unknown_parameters_rejected_when_strict(client, monkeypatch):
    """With REJECT_UNKNOWN_PARAMS (DALI-1.2), unknown parameters are an error."""
    monkeypatch.setattr(get_settings(), "REJECT_UNKNOWN_PARAMS", True)
    response = client.get(f"{SEARCH}?{VALID}&FOO=1")
    assert response.status_code == 400
    assert "FOO" in response.text


# --- Errors ---------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "query",
    [
        "DEC=20&SR=0.05",  # missing RA
        "RA=10&SR=0.05",  # missing DEC
        "RA=10&DEC=20",  # missing SR
        "RA=abc&DEC=20&SR=0.05",  # unparseable
        "RA=10&DEC=91&SR=0.05",  # out of range
        "RA=-1&DEC=20&SR=0.05",
        "RA=10&DEC=20&SR=-0.1",
        "RA=10&DEC=20&SR=10",  # larger than maxSR
        f"{VALID}&MAXREC=-1",
        f"{VALID}&VERB=4",
        f"{VALID}&RESPONSEFORMAT=text/csv",  # unsupported format
        f"{VALID}&RA=11",  # repeated single-valued parameter
        "ra=10&dec=20&sr=0.05",  # parameter names are case-sensitive (DALI-1.2)
    ],
)
def test_bad_requests_are_plain_text_400(client, query):
    """Invalid requests return 400 with a text/plain error document."""
    response = client.get(f"{SEARCH}?{query}")
    assert response.status_code == 400
    assert response.headers["content-type"].startswith("text/plain")
    assert response.text.strip()


def test_server_error_is_plain_text(client, fake_session, monkeypatch):
    """Unexpected failures return 500 with a text/plain error document."""

    def broken(*args, **kwargs):
        raise RuntimeError("database exploded")

    monkeypatch.setattr(fake_session, "execute", broken)
    response = client.get(f"{SEARCH}?{VALID}")
    assert response.status_code == 500
    assert response.headers["content-type"].startswith("text/plain")
    assert "exploded" not in response.text


# --- OpenAPI document -----------------------------------------------------------------------------


def test_openapi_document_shape(client):
    """The generated OpenAPI mirrors the SCS 1.1 document: a /search path with 200 and 400 responses only."""
    spec = client.get("/openapi.json").json()
    assert spec["info"]["version"] == "1.1"
    operation = spec["paths"]["/search"]["get"]
    assert [p["name"] for p in operation["parameters"]] == ["RA", "DEC", "SR", "MAXREC", "RESPONSEFORMAT", "VERB"]
    assert set(operation["responses"]) == {"200", "400"}
    assert "application/x-votable+xml" in operation["responses"]["200"]["content"]
    assert "text/plain" in operation["responses"]["400"]["content"]
