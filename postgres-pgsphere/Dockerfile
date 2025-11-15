# Start from official Postgres image
FROM postgres:17

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    git \
    make \
    gcc \
    g++ \
    libc6-dev \
    libpq-dev \
    postgresql-server-dev-17 \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Build and install pgSphere from source
RUN git clone https://github.com/postgrespro/pgsphere.git /tmp/pgsphere \
    && cd /tmp/pgsphere \
    && make USE_HEALPIX=0 \
    && make USE_HEALPIX=0 install \
    && rm -rf /tmp/pgsphere

COPY init-db/ /docker-entrypoint-initdb.d
