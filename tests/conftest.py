"""Shared test fixtures.

The tests exercise the SCS 1.1 protocol layer with a fake database session, so they need no database.
"""

import os

# The engine is created at import time; it never connects in these tests.
os.environ.setdefault("DATABASE_URL", "postgresql://user@localhost/unused")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from fastapi_scs.dependencies import get_session  # noqa: E402
from fastapi_scs.main import app, scs_app  # noqa: E402

FAKE_ROWS = [
    {"name": f"src{i}", "ra": 10.0 + i * 0.001, "dec": 20.0, "flux": float(i), "id": i} for i in range(5)
]


class FakeResult:
    """Stand-in for a SQLAlchemy result."""

    def __init__(self, rows):
        self._rows = rows

    def mappings(self):
        """Mimic Result.mappings()."""
        return self

    def all(self):
        """Mimic MappingResult.all()."""
        return self._rows


class FakeSession:
    """Records queries and returns FAKE_ROWS, honouring the LIMIT parameter."""

    def __init__(self):
        self.calls = []

    def execute(self, query, params):
        """Mimic Session.execute()."""
        self.calls.append((str(query), params))
        columns = [c.strip() for c in str(query).split("SELECT", 1)[1].split("FROM", 1)[0].split(",")]
        rows = [{c: row[c] for c in columns} for row in FAKE_ROWS]
        return FakeResult(rows[: params["limit"]])


@pytest.fixture
def fake_session():
    """A fake session injected in place of the database."""
    session = FakeSession()
    scs_app.dependency_overrides[get_session] = lambda: session
    yield session
    scs_app.dependency_overrides.clear()


@pytest.fixture
def client(fake_session):  # pylint: disable=unused-argument,redefined-outer-name
    """Test client for the full application."""
    return TestClient(app, raise_server_exceptions=False)
