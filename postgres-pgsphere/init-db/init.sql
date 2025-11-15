CREATE EXTENSION IF NOT EXISTS pg_sphere;

CREATE TABLE IF NOT EXISTS sources (
    id SERIAL PRIMARY KEY,
    ra DOUBLE PRECISION NOT NULL,
    dec DOUBLE PRECISION NOT NULL,
    flux DOUBLE PRECISION,
    name TEXT,
    coord spoint
);

-- Populate with dummy data
INSERT INTO sources (ra, dec, flux, name)
SELECT
    random() * 360,
    (random() * 180) - 90,
    random() * 1000,
    md5(random()::text)
FROM generate_series(1, 1000);

UPDATE sources
SET coord = spoint(ra, dec);

CREATE INDEX sources_coord_idx ON sources USING GIST (coord);


