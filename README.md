# FastAPI-SCS

This project is a Python implementation of the IVOA Simple Cone Search (SCS) standard using [FastAPI](https://fastapi.tiangolo.com/).

## Features

- Implements the IVOA SCS protocol.
- Includes simulated data via a PostgreSQL database for testing.

## Getting Started

Running the project with docker-compose is the recommended way to get started quickly. It sets up a PostgreSQL database with simulated data and runs the FastAPI application. By default, the api will be available at `http://localhost:8000/conesearch`.

Interactive Swagger documentation is available at `http://localhost:8000/docs`.

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
pip install - requirements.txt
pip install -e .
uvicorn fastapi_scs.main:app --reload
```

## License

See [LICENSE](./LICENSE) for details.