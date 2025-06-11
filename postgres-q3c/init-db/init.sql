CREATE EXTENSION IF NOT EXISTS q3c;

CREATE TABLE IF NOT EXISTS sources (
    id SERIAL PRIMARY KEY,
    ra DOUBLE PRECISION NOT NULL,
    dec DOUBLE PRECISION NOT NULL,
    flux DOUBLE PRECISION,
    name TEXT
);

-- Populate with dummy data
INSERT INTO sources (ra, dec, flux, name)
SELECT
    random() * 360,
    (random() * 180) - 90,
    random() * 1000,
    md5(random()::text)
FROM generate_series(1, 1000);
