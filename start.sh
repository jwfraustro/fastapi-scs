#!/bin/sh
set -e

uvicorn fastapi_scs.main:app --host "" --port ${PORT:-8000}