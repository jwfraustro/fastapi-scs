FROM postgres:16

# Install build tools and required libraries
RUN apt-get update && apt-get install -y \
    git \
    make \
    gcc \
    postgresql-server-dev-16 \
    libzstd-dev \
    liblz4-dev \
    zlib1g-dev \
    libreadline-dev \
    && rm -rf /var/lib/apt/lists/*

# Clone and install Q3C
RUN git clone https://github.com/segasai/q3c.git /q3c \
    && cd /q3c && make && make install \
    && rm -rf /q3c

COPY init-db/ /docker-entrypoint-initdb.d