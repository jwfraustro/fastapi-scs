# FastAPI-SCS

This project is a Python implementation of the IVOA Simple Cone Search (SCS) standard using [FastAPI](https://fastapi.tiangolo.com/).

This branch targets the draft **ConeSearch-1.1** and its [OpenAPI definition](https://github.com/molinaro-m/ConeSearch/tree/conesearch-openapi/openapi). It is meant to show that the 1.1 definition is implementable and roughly what an implementation looks like: the column metadata (`fastapi_scs/service.py`) and the database are placeholders for a real catalogue.

This minimal example has been validated by both VOParis and ESA Euro-VO tools and is compliant with the IVOA SCS standard.

## Features

- Implements the IVOA SCS 1.1 protocol (`GET /search`).
- Parameters `RA`, `DEC`, `SR` (decimal degrees), plus DALI `MAXREC` and `RESPONSEFORMAT`, and `VERB` (default 2).
- VOTable responses (`application/x-votable+xml`) with `QUERY_STATUS` (`OK`/`OVERFLOW`) and the SCS 1.1 UCD1+ columns.
- `SR=0` and `MAXREC=0` return the response metadata only.
- Errors are `text/plain` documents with an appropriate HTTP status code (400 for invalid requests).
- Parameter names are case-sensitive (DALI-1.2).
- Includes simulated data via a PostgreSQL+pgSphere database for testing.

## Configuration

Settings are read from environment variables (or a `.env` file):

| Setting | Default | Meaning |
|---|---|---|
| `DATABASE_URL` | | SQLAlchemy database URL |
| `ROOT_PATH` | | Path prefix when served behind a proxy; it appears as the `servers` URL in the generated OpenAPI |
| `MAX_SR` | `0.1` | Largest accepted search radius, in degrees (maxSR) |
| `DEFAULT_MAXREC` | `1000` | Row limit when `MAXREC` is not given |
| `MAX_MAXREC` | `10000` | Hard row limit |
| `CASE_INSENSITIVE_PARAMS` | `false` | Accept parameter names in any case (pre-DALI-1.2 behaviour) |
| `REJECT_UNKNOWN_PARAMS` | `false` | Reject unknown parameters (DALI-1.2) instead of ignoring them with an `INFO name="warning"` (SCS 1.1) |

## Getting Started

Running the project with docker-compose is the recommended way to get started quickly. It sets up a PostgreSQL database with simulated data and runs the FastAPI application. By default, the api will be available at `http://localhost:8000/search`, e.g. `http://localhost:8000/search?RA=180&DEC=0&SR=0.1`.

Interactive Swagger documentation is available at `http://localhost:8000/docs`, and the generated OpenAPI document at `http://localhost:8000/openapi.json`.

### Requirements

- Python 3.8+
- [Docker Compose](https://docs.docker.com/compose/) (optional)
- [Conda](https://docs.conda.io/) (optional)

### Running with Docker Compose

```bash
docker-compose up
```

### Running with Conda

```bash
conda env create -f environment.yml
conda activate fastapi-scs
pip install -r requirements.txt
pip install -e .
uvicorn fastapi_scs.main:app --reload
```

### Running the tests

The tests use a fake database session, so no database is needed:

```bash
pip install pytest "httpx<0.28"
pytest tests
```

## License

See [LICENSE](./LICENSE) for details.