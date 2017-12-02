
SELECT * FROM census_2016_data.metadata_stats WHERE lower(long_id) LIKE '%relig%' AND column_heading_description = 'Persons' ORDER BY sequential_id;

SELECT * FROM census_2016_data.metadata_stats WHERE table_number = 'G14' AND column_heading_description = 'Persons' ORDER BY sequential_id;


select SUM(G5447) from census_2016_data.sa1_G14;


-- no religion

DROP TABLE IF EXISTS census_2016_sandpit.dots_non_religious;
WITH temp_sa1 AS (
  SELECT tab.G5447::integer as val,
    ST_Buffer(ST_SnapToGrid(bdy.geom, 0.0001), 0.0) As geom
    FROM census_2016_bdys.sa1_2016_aust AS bdy
    INNER JOIN census_2016_data.sa1_G14 AS tab ON bdy.sa1_7dig16 = tab.region_id
    WHERE tab.G5447::integer > 0
    AND bdy.ste_code16 IN ('1', '8')
    AND NOT ST_IsEmpty(geom)
)
SELECT row_number() OVER () as gid,
  ST_GeneratePoints(geom, val) As geom
  INTO census_2016_sandpit.dots_non_religious
  FROM temp_sa1
  WHERE ST_Area(ST_Envelope(geom)) > 0.0;

ALTER TABLE census_2016_sandpit.dots_non_religious OWNER to postgres;
ALTER TABLE census_2016_sandpit.dots_non_religious ADD CONSTRAINT dots_non_religious_pkey PRIMARY KEY (gid);
CREATE INDEX dots_non_religious_geom_idx ON census_2016_sandpit.dots_non_religious USING gist (geom);
ALTER TABLE census_2016_sandpit.dots_non_religious CLUSTER ON dots_non_religious_geom_idx;


-- christianity

DROP TABLE IF EXISTS census_2016_sandpit.dots_christian;
WITH temp_sa1 AS (
  SELECT tab.G5423::integer as val,
    ST_Buffer(ST_SnapToGrid(bdy.geom, 0.0001), 0.0) As geom
    FROM census_2016_bdys.sa1_2016_aust AS bdy
    INNER JOIN census_2016_data.sa1_G14 AS tab ON bdy.sa1_7dig16 = tab.region_id
    WHERE tab.G5423::integer > 0
    AND bdy.ste_code16 IN ('1', '8')
    AND NOT ST_IsEmpty(geom)
)
SELECT row_number() OVER () as gid,
  ST_GeneratePoints(geom, val) As geom
  INTO census_2016_sandpit.dots_christian
  FROM temp_sa1
  WHERE ST_Area(ST_Envelope(geom)) > 0.0;

ALTER TABLE census_2016_sandpit.dots_christian OWNER to postgres;
ALTER TABLE census_2016_sandpit.dots_christian ADD CONSTRAINT dots_christian_pkey PRIMARY KEY (gid);
CREATE INDEX dots_christian_geom_idx ON census_2016_sandpit.dots_christian USING gist (geom);
ALTER TABLE census_2016_sandpit.dots_christian CLUSTER ON dots_christian_geom_idx;


-- islam

DROP TABLE IF EXISTS census_2016_sandpit.dots_islam;
WITH temp_sa1 AS (
  SELECT tab.G5429::integer as val,
    ST_Buffer(ST_SnapToGrid(bdy.geom, 0.0001), 0.0) As geom
    FROM census_2016_bdys.sa1_2016_aust AS bdy
    INNER JOIN census_2016_data.sa1_G14 AS tab ON bdy.sa1_7dig16 = tab.region_id
    WHERE tab.G5429::integer > 0
    AND bdy.ste_code16 IN ('1', '8')
    AND NOT ST_IsEmpty(geom)
)
SELECT row_number() OVER () as gid,
  ST_GeneratePoints(geom, val) As geom
  INTO census_2016_sandpit.dots_islam
  FROM temp_sa1
  WHERE ST_Area(ST_Envelope(geom)) > 0.0;

ALTER TABLE census_2016_sandpit.dots_islam OWNER to postgres;
ALTER TABLE census_2016_sandpit.dots_islam ADD CONSTRAINT dots_islam_pkey PRIMARY KEY (gid);
CREATE INDEX dots_islam_geom_idx ON census_2016_sandpit.dots_islam USING gist (geom);
ALTER TABLE census_2016_sandpit.dots_islam CLUSTER ON dots_islam_geom_idx;


-- buddhism

DROP TABLE IF EXISTS census_2016_sandpit.dots_buddhism;
WITH temp_sa1 AS (
  SELECT tab.G5363::integer as val,
    ST_Buffer(ST_SnapToGrid(bdy.geom, 0.0001), 0.0) As geom
    FROM census_2016_bdys.sa1_2016_aust AS bdy
    INNER JOIN census_2016_data.sa1_G14 AS tab ON bdy.sa1_7dig16 = tab.region_id
    WHERE tab.G5363::integer > 0
    AND bdy.ste_code16 IN ('1', '8')
    AND NOT ST_IsEmpty(geom)
)
SELECT row_number() OVER () as gid,
  ST_GeneratePoints(geom, val) As geom
  INTO census_2016_sandpit.dots_buddhism
  FROM temp_sa1
  WHERE ST_Area(ST_Envelope(geom)) > 0.0;

ALTER TABLE census_2016_sandpit.dots_buddhism OWNER to postgres;
ALTER TABLE census_2016_sandpit.dots_buddhism ADD CONSTRAINT dots_buddhism_pkey PRIMARY KEY (gid);
CREATE INDEX dots_buddhism_geom_idx ON census_2016_sandpit.dots_buddhism USING gist (geom);
ALTER TABLE census_2016_sandpit.dots_buddhism CLUSTER ON dots_buddhism_geom_idx;


-- hinduism

DROP TABLE IF EXISTS census_2016_sandpit.dots_hinduism;
WITH temp_sa1 AS (
  SELECT tab.G5426::integer as val,
    ST_Buffer(ST_SnapToGrid(bdy.geom, 0.0001), 0.0) As geom
    FROM census_2016_bdys.sa1_2016_aust AS bdy
    INNER JOIN census_2016_data.sa1_G14 AS tab ON bdy.sa1_7dig16 = tab.region_id
    WHERE tab.G5426::integer > 0
    AND bdy.ste_code16 IN ('1', '8')
    AND NOT ST_IsEmpty(geom)
)
SELECT row_number() OVER () as gid,
  ST_GeneratePoints(geom, val) As geom
  INTO census_2016_sandpit.dots_hinduism
  FROM temp_sa1
  WHERE ST_Area(ST_Envelope(geom)) > 0.0;

ALTER TABLE census_2016_sandpit.dots_hinduism OWNER to postgres;
ALTER TABLE census_2016_sandpit.dots_hinduism ADD CONSTRAINT dots_hinduism_pkey PRIMARY KEY (gid);
CREATE INDEX dots_hinduism_geom_idx ON census_2016_sandpit.dots_hinduism USING gist (geom);
ALTER TABLE census_2016_sandpit.dots_hinduism CLUSTER ON dots_hinduism_geom_idx;


-- judaism

DROP TABLE IF EXISTS census_2016_sandpit.dots_judaism;
WITH temp_sa1 AS (
  SELECT tab.G5432::integer as val,
    ST_Buffer(ST_SnapToGrid(bdy.geom, 0.0001), 0.0) As geom
    FROM census_2016_bdys.sa1_2016_aust AS bdy
    INNER JOIN census_2016_data.sa1_G14 AS tab ON bdy.sa1_7dig16 = tab.region_id
    WHERE tab.G5432::integer > 0
    AND bdy.ste_code16 IN ('1', '8')
    AND NOT ST_IsEmpty(geom)
)
SELECT row_number() OVER () as gid,
  ST_GeneratePoints(geom, val) As geom
  INTO census_2016_sandpit.dots_judaism
  FROM temp_sa1
  WHERE ST_Area(ST_Envelope(geom)) > 0.0;

ALTER TABLE census_2016_sandpit.dots_judaism OWNER to postgres;
ALTER TABLE census_2016_sandpit.dots_judaism ADD CONSTRAINT dots_judaism_pkey PRIMARY KEY (gid);
CREATE INDEX dots_judaism_geom_idx ON census_2016_sandpit.dots_judaism USING gist (geom);
ALTER TABLE census_2016_sandpit.dots_judaism CLUSTER ON dots_judaism_geom_idx;
