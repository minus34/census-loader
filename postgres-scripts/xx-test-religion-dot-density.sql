
SELECT * FROM census_2016_data.metadata_stats WHERE lower(long_id) LIKE '%relig%' AND column_heading_description = 'Persons' ORDER BY sequential_id;

SELECT * FROM census_2016_data.metadata_stats WHERE table_number = 'G14' AND column_heading_description = 'Persons' ORDER BY sequential_id;


select SUM(G5447) from census_2016_data.sa1_G14;


-- no religion

DROP TABLE IF EXISTS census_2016_sandpit.temp_sa1; -- 55706
SELECT row_number() OVER () as gid,
  bdy.sa1_7dig16,
  tab.G5447::integer as val,
  ST_Buffer(ST_SnapToGrid(bdy.geom, 0.0001), 0.0) As geom
  INTO census_2016_sandpit.temp_sa1
  FROM census_2016_bdys.sa1_2016_aust AS bdy
  INNER JOIN census_2016_data.sa1_G14 AS tab ON bdy.sa1_7dig16 = tab.region_id
  WHERE tab.G5447::integer > 0
  AND NOT ST_IsEmpty(geom);

DROP TABLE IF EXISTS census_2016_sandpit.dots_non_religious;
SELECT row_number() OVER () as gid,
  ST_RandomPointsInPolygon(geom, val) As geom
  INTO census_2016_sandpit.dots_non_religious
  FROM census_2016_sandpit.temp_sa1
  WHERE ST_Area(ST_Envelope(geom)) > 0.0;

--ALTER TABLE census_2016_sandpit.dots_non_religiou ADD CONSTRAINT dots_non_religiou_pkey PRIMARY KEY (gid);
ALTER TABLE census_2016_sandpit.dots_non_religious OWNER to postgres;

CREATE INDEX dots_non_religious_geom_idx
    ON census_2016_sandpit.dots_non_religious USING gist (geom);

ALTER TABLE census_2016_sandpit.dots_non_religious
    CLUSTER ON dots_non_religious_geom_idx;
    

-- christianity

DROP TABLE IF EXISTS census_2016_sandpit.temp_sa1; -- 55706
SELECT row_number() OVER () as gid,
  bdy.sa1_7dig16,
  tab.G5447::integer as val,
  ST_Buffer(ST_SnapToGrid(bdy.geom, 0.0001), 0.0) As geom
  INTO census_2016_sandpit.temp_sa1
  FROM census_2016_bdys.sa1_2016_aust AS bdy
  INNER JOIN census_2016_data.sa1_G14 AS tab ON bdy.sa1_7dig16 = tab.region_id
  WHERE tab.G5447::integer > 0
  AND NOT ST_IsEmpty(geom);

DROP TABLE IF EXISTS census_2016_sandpit.dots_non_religious;
SELECT row_number() OVER () as gid,
  ST_RandomPointsInPolygon(geom, val) As geom
  INTO census_2016_sandpit.dots_non_religious
  FROM census_2016_sandpit.temp_sa1
  WHERE ST_Area(ST_Envelope(geom)) > 0.0;

--ALTER TABLE census_2016_sandpit.dots_non_religious_g5423 ADD CONSTRAINT dots_non_religious_g5423_pkey PRIMARY KEY (gid);
ALTER TABLE census_2016_sandpit.dots_non_religious OWNER to postgres;

CREATE INDEX dots_non_religious_geom_idx
    ON census_2016_sandpit.dots_non_religious USING gist (geom);

ALTER TABLE census_2016_sandpit.dots_non_religious
    CLUSTER ON dots_non_religious_g5423_geom_idx;
    



