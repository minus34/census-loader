--
-- SELECT * FROM census_2016_data.metadata_stats WHERE lower(long_id) LIKE '%relig%' AND column_heading_description = 'Persons' ORDER BY sequential_id;
--
-- SELECT * FROM census_2016_data.metadata_stats WHERE table_number = 'G14' AND column_heading_description = 'Persons' ORDER BY sequential_id;
--
--
-- select SUM(G5447) from census_2016_data.sa1_G14;


-- the entire population

DROP TABLE IF EXISTS census_2016_sandpit.dots_population;
WITH temp_sa1 AS (
  SELECT tab.region_id AS id, tab.G5462::integer as val,
    bdy.geom
    FROM census_2016_bdys.sa1_2016_aust AS bdy
    INNER JOIN census_2016_data.sa1_G14 AS tab ON bdy.sa1_7dig16 = tab.region_id
    WHERE tab.G5462::integer > 0
    -- AND bdy.ste_code16 IN ('1', '8')
    AND NOT ST_IsEmpty(geom)
)
SELECT id, NULL::numeric(7,5) AS latitude, NULL::numeric(8,5) AS longitude,
  (ST_Dump(ST_GeneratePoints(geom, (val/10)::integer))).geom AS geom
  INTO census_2016_sandpit.dots_population
  FROM temp_sa1
  WHERE ST_Area(ST_Envelope(geom)) > 0.0;

UPDATE census_2016_sandpit.dots_population
  SET latitude = ST_Y(geom),
    longitude = ST_X(geom);

ALTER TABLE census_2016_sandpit.dots_population OWNER to postgres;
-- ALTER TABLE census_2016_sandpit.dots_population ADD CONSTRAINT dots_population_pkey PRIMARY KEY (id);
CREATE INDEX dots_population_geom_idx ON census_2016_sandpit.dots_population USING gist (geom);
ALTER TABLE census_2016_sandpit.dots_population CLUSTER ON dots_population_geom_idx;

ANALYZE census_2016_sandpit.dots_population;


-- no religion

DROP TABLE IF EXISTS census_2016_sandpit.dots_non_religious;
WITH temp_sa1 AS (
  SELECT tab.region_id AS id, tab.G5447::integer as val,
    bdy.geom
    FROM census_2016_bdys.sa1_2016_aust AS bdy
    INNER JOIN census_2016_data.sa1_G14 AS tab ON bdy.sa1_7dig16 = tab.region_id
    WHERE tab.G5447::integer > 0
    -- AND bdy.ste_code16 IN ('1', '8')
    AND NOT ST_IsEmpty(geom)
)
SELECT id, NULL::numeric(7,5) AS latitude, NULL::numeric(8,5) AS longitude,
  (ST_Dump(ST_GeneratePoints(geom, (val/10)::integer))).geom AS geom
  INTO census_2016_sandpit.dots_non_religious
  FROM temp_sa1
  WHERE ST_Area(ST_Envelope(geom)) > 0.0;

UPDATE census_2016_sandpit.dots_non_religious
SET latitude = ST_Y(geom),
  longitude = ST_X(geom);

ALTER TABLE census_2016_sandpit.dots_non_religious OWNER to postgres;
-- ALTER TABLE census_2016_sandpit.dots_non_religious ADD CONSTRAINT dots_non_religious_pkey PRIMARY KEY (id);
CREATE INDEX dots_non_religious_geom_idx ON census_2016_sandpit.dots_non_religious USING gist (geom);
ALTER TABLE census_2016_sandpit.dots_non_religious CLUSTER ON dots_non_religious_geom_idx;

ANALYZE census_2016_sandpit.dots_non_religious;


-- christianity

DROP TABLE IF EXISTS census_2016_sandpit.dots_christian;
WITH temp_sa1 AS (
  SELECT tab.region_id AS id, tab.G5423::integer as val,
    bdy.geom
    FROM census_2016_bdys.sa1_2016_aust AS bdy
    INNER JOIN census_2016_data.sa1_G14 AS tab ON bdy.sa1_7dig16 = tab.region_id
    WHERE tab.G5423::integer > 0
    -- AND bdy.ste_code16 IN ('1', '8')
    AND NOT ST_IsEmpty(geom)
)
SELECT id, NULL::numeric(7,5) AS latitude, NULL::numeric(8,5) AS longitude,
  (ST_Dump(ST_GeneratePoints(geom, (val/10)::integer))).geom AS geom
  INTO census_2016_sandpit.dots_christian
  FROM temp_sa1
  WHERE ST_Area(ST_Envelope(geom)) > 0.0;

UPDATE census_2016_sandpit.dots_christian
  SET latitude = ST_Y(geom),
    longitude = ST_X(geom);

ALTER TABLE census_2016_sandpit.dots_christian OWNER to postgres;
-- ALTER TABLE census_2016_sandpit.dots_christian ADD CONSTRAINT dots_christian_pkey PRIMARY KEY (id);
CREATE INDEX dots_christian_geom_idx ON census_2016_sandpit.dots_christian USING gist (geom);
ALTER TABLE census_2016_sandpit.dots_christian CLUSTER ON dots_christian_geom_idx;

ANALYZE census_2016_sandpit.dots_christian;


-- islam

DROP TABLE IF EXISTS census_2016_sandpit.dots_islam;
WITH temp_sa1 AS (
  SELECT tab.region_id AS id, tab.G5429::integer as val,
    bdy.geom
    FROM census_2016_bdys.sa1_2016_aust AS bdy
    INNER JOIN census_2016_data.sa1_G14 AS tab ON bdy.sa1_7dig16 = tab.region_id
    WHERE tab.G5429::integer > 0
    -- AND bdy.ste_code16 IN ('1', '8')
    AND NOT ST_IsEmpty(geom)
)
SELECT id, NULL::numeric(7,5) AS latitude, NULL::numeric(8,5) AS longitude,
  (ST_Dump(ST_GeneratePoints(geom, (val/10)::integer))).geom AS geom
  INTO census_2016_sandpit.dots_islam
  FROM temp_sa1
  WHERE ST_Area(ST_Envelope(geom)) > 0.0;

UPDATE census_2016_sandpit.dots_islam
  SET latitude = ST_Y(geom),
    longitude = ST_X(geom);

ALTER TABLE census_2016_sandpit.dots_islam OWNER to postgres;
-- ALTER TABLE census_2016_sandpit.dots_islam ADD CONSTRAINT dots_islam_pkey PRIMARY KEY (id);
CREATE INDEX dots_islam_geom_idx ON census_2016_sandpit.dots_islam USING gist (geom);
ALTER TABLE census_2016_sandpit.dots_islam CLUSTER ON dots_islam_geom_idx;

ANALYZE census_2016_sandpit.dots_islam;


-- buddhism

DROP TABLE IF EXISTS census_2016_sandpit.dots_buddhism;
WITH temp_sa1 AS (
  SELECT tab.region_id AS id, tab.G5363::integer as val,
    bdy.geom
    FROM census_2016_bdys.sa1_2016_aust AS bdy
    INNER JOIN census_2016_data.sa1_G14 AS tab ON bdy.sa1_7dig16 = tab.region_id
    WHERE tab.G5363::integer > 0
    -- AND bdy.ste_code16 IN ('1', '8')
    AND NOT ST_IsEmpty(geom)
)
SELECT id, NULL::numeric(7,5) AS latitude, NULL::numeric(8,5) AS longitude,
  (ST_Dump(ST_GeneratePoints(geom, (val/10)::integer))).geom AS geom
  INTO census_2016_sandpit.dots_buddhism
  FROM temp_sa1
  WHERE ST_Area(ST_Envelope(geom)) > 0.0;

UPDATE census_2016_sandpit.dots_buddhism
       SET latitude = ST_Y(geom),
longitude = ST_X(geom);

ALTER TABLE census_2016_sandpit.dots_buddhism OWNER to postgres;
-- ALTER TABLE census_2016_sandpit.dots_buddhism ADD CONSTRAINT dots_buddhism_pkey PRIMARY KEY (id);
CREATE INDEX dots_buddhism_geom_idx ON census_2016_sandpit.dots_buddhism USING gist (geom);
ALTER TABLE census_2016_sandpit.dots_buddhism CLUSTER ON dots_buddhism_geom_idx;

ANALYZE census_2016_sandpit.dots_buddhism;


-- hinduism

DROP TABLE IF EXISTS census_2016_sandpit.dots_hinduism;
WITH temp_sa1 AS (
  SELECT tab.region_id AS id, tab.G5426::integer as val,
    bdy.geom
    FROM census_2016_bdys.sa1_2016_aust AS bdy
    INNER JOIN census_2016_data.sa1_G14 AS tab ON bdy.sa1_7dig16 = tab.region_id
    WHERE tab.G5426::integer > 0
    -- AND bdy.ste_code16 IN ('1', '8')
    AND NOT ST_IsEmpty(geom)
)
SELECT id, NULL::numeric(7,5) AS latitude, NULL::numeric(8,5) AS longitude,
  (ST_Dump(ST_GeneratePoints(geom, (val/10)::integer))).geom AS geom
  INTO census_2016_sandpit.dots_hinduism
  FROM temp_sa1
  WHERE ST_Area(ST_Envelope(geom)) > 0.0;

UPDATE census_2016_sandpit.dots_hinduism
       SET latitude = ST_Y(geom),
longitude = ST_X(geom);

ALTER TABLE census_2016_sandpit.dots_hinduism OWNER to postgres;
-- ALTER TABLE census_2016_sandpit.dots_hinduism ADD CONSTRAINT dots_hinduism_pkey PRIMARY KEY (id);
CREATE INDEX dots_hinduism_geom_idx ON census_2016_sandpit.dots_hinduism USING gist (geom);
ALTER TABLE census_2016_sandpit.dots_hinduism CLUSTER ON dots_hinduism_geom_idx;

ANALYZE census_2016_sandpit.dots_hinduism;


-- judaism

DROP TABLE IF EXISTS census_2016_sandpit.dots_judaism;
WITH temp_sa1 AS (
  SELECT tab.region_id AS id, tab.G5432::integer as val,
    bdy.geom
    FROM census_2016_bdys.sa1_2016_aust AS bdy
    INNER JOIN census_2016_data.sa1_G14 AS tab ON bdy.sa1_7dig16 = tab.region_id
    WHERE tab.G5432::integer > 0
    -- AND bdy.ste_code16 IN ('1', '8')
    AND NOT ST_IsEmpty(geom)
)
SELECT id, NULL::numeric(7,5) AS latitude, NULL::numeric(8,5) AS longitude,
  (ST_Dump(ST_GeneratePoints(geom, (val/10)::integer))).geom AS geom
  INTO census_2016_sandpit.dots_judaism
  FROM temp_sa1
  WHERE ST_Area(ST_Envelope(geom)) > 0.0;

UPDATE census_2016_sandpit.dots_judaism
       SET latitude = ST_Y(geom),
longitude = ST_X(geom);

ALTER TABLE census_2016_sandpit.dots_judaism OWNER to postgres;
-- ALTER TABLE census_2016_sandpit.dots_judaism ADD CONSTRAINT dots_judaism_pkey PRIMARY KEY (id);
CREATE INDEX dots_judaism_geom_idx ON census_2016_sandpit.dots_judaism USING gist (geom);
ALTER TABLE census_2016_sandpit.dots_judaism CLUSTER ON dots_judaism_geom_idx;

ANALYZE census_2016_sandpit.dots_judaism;

-- select Count(*) as cnt from census_2016_sandpit.dots_judaism;

-- SELECT * FROM census_2016_bdys.sa1_2016_aust
--   WHERE ST_Area(ST_Buffer(ST_SnapToGrid(geom, 0.0001), 0.0))/ST_Area(ST_Envelope(ST_Buffer(ST_SnapToGrid(geom, 0.0001), 0.0))) < 0.0001;

COPY (
-- 	SELECT 'Christian' AS religion, latitude, longitude FROM census_2016_sandpit.dots_christian
-- 	UNION ALL
	SELECT 'Judaism' AS religion, latitude, longitude FROM census_2016_sandpit.dots_judaism
	UNION ALL
	SELECT 'Islam' AS religion, latitude, longitude FROM census_2016_sandpit.dots_islam
	UNION ALL
	SELECT 'Hinduism' AS religion, latitude, longitude FROM census_2016_sandpit.dots_hinduism
	UNION ALL
	SELECT 'Buddhism' AS religion, latitude, longitude FROM census_2016_sandpit.dots_buddhism
-- 	UNION ALL
-- 	SELECT 'No Religion' AS religion, latitude, longitude FROM census_2016_sandpit.dots_non_religious
) TO '/Users/hugh.saalmans/tmp/abs_census_2016_data/religion_dots.csv' CSV HEADER;

-- DROP MATERIALIZED VIEW IF EXISTS census_2016_sandpit.mv_dots_religion;
-- CREATE MATERIALIZED VIEW census_2016_sandpit.mv_dots_religion AS
-- SELECT 'Christian' AS religion, latitude, longitude FROM census_2016_sandpit.dots_christian
--   UNION ALL
-- SELECT 'Judaism' AS religion, latitude, longitude FROM census_2016_sandpit.dots_judaism
-- UNION ALL
-- SELECT 'Islam' AS religion, latitude, longitude FROM census_2016_sandpit.dots_islam
-- UNION ALL
-- SELECT 'Hinduism' AS religion, latitude, longitude FROM census_2016_sandpit.dots_hinduism
-- UNION ALL
-- SELECT 'Buddhism' AS religion, latitude, longitude FROM census_2016_sandpit.dots_buddhism
-- UNION ALL
-- SELECT 'No Religion' AS religion, latitude, longitude FROM census_2016_sandpit.dots_non_religious;
-- 
-- ALTER TABLE census_2016_sandpit.mv_dots_religion OWNER to postgres;
-- CREATE INDEX mv_dots_religion_lat_long_idx ON census_2016_sandpit.mv_dots_religion USING btree (latitude, longitude);
-- ALTER TABLE census_2016_sandpit.mv_dots_religion CLUSTER ON mv_dots_religion_lat_long_idx;
