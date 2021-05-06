
-- create table of RA bdys with a 1km buffer
drop table if exists census_2016_bdys.ra_2016_aust_buffer;
create table census_2016_bdys.ra_2016_aust_buffer as
select gid,
       ra_code16,
       ra_name16,
       ste_code16,
       ste_name16,
       areasqkm16,
       ST_Transform(ST_Buffer(geom::geography, 1000.0)::geometry, 4283) as geom
from census_2016_bdys.ra_2016_aust
;

CREATE INDEX ra_2016_aust_buffer_geom_idx ON census_2016_bdys.ra_2016_aust_buffer USING spgist (geom);
ALTER TABLE census_2016_bdys.ra_2016_aust_buffer CLUSTER ON ra_2016_aust_buffer_geom_idx;
