

select *
from census_2021_data.metadata_tables
;

select *
from census_2021_data.metadata_stats
where sequential_id = 'G10065'
;

select count(*),
       substring(sequential_id, 1,1) as profile
from census_2021_data.metadata_stats
group by profile
;


select *
from census_2021_data.add_g01;

select *
from census_2021_data.ireg_i01a;

select *
from census_2021_bdys_gda94.poa_2021_aust_gda94
;

UPDATE census_2021_bdys_gda94.iare_2021_aust_gda94
SET iare_code_2021 = upper('iare') || iare_code_2021
                           WHERE substring(iare_code_2021, 1 , 3) <> upper('iare')



WITH mvtgeom AS
         (
             SELECT ST_AsMVTGeom(geom, ST_TileEnvelope(12, 513, 412)) AS geom,
                    sa1_code_2021,
                    state_name_2021
             FROM census_2021_bdys.sa1_2021_aust_gda94
         )
SELECT ST_AsMVT(mvtgeom.*)
FROM mvtgeom;


select count(*) as num_geoms,
       sum(st_npoints(geom))
--        sum(st_npoints(st_simplifyvw(geom, 0.0000001))),
--        sum(st_npoints(st_simplify(geom, 0.00005))),
--        sum(st_npoints(st_simplifypreservetopology(geom, 0.00005)))
from census_2021_bdys.sa1_2021_aust_gda94
;

-- +---------+-------+
-- |num_geoms|sum    |
-- +---------+-------+
-- |61811    |9400814|
-- +---------+-------+

select count(*) as num_geoms,
       sum(st_npoints(geom))
from testing.sa1_thinned
;

-- +---------+-------+
-- |num_geoms|sum    |
-- +---------+-------+
-- |61811    |3671235|
-- +---------+-------+


-- create thinned polygons
drop table if exists testing.sa1_2021_aust_gda94_web;
create table testing.sa1_2021_aust_gda94_web as
select sa1_code_2021,
       st_simplifyvw(geom, 0.0000001) as geom
from census_2021_bdys.sa1_2021_aust_gda94
;
analyse testing.sa1_2021_aust_gda94_web;

alter table testing.sa1_2021_aust_gda94_web add constraint sa1_2021_aust_gda94_web_pkey primary key (sa1_code_2021)
create index sa1_2021_aust_gda94_web_gist on testing.sa1_2021_aust_gda94_web using gist(geom);
alter table testing.sa1_2021_aust_gda94_web cluster on sa1_2021_aust_gda94_web_gist;


-- attempted topology based simplification - still too slow/doesn't finish for SA1s
--
-- -- STEP 1 - create new table with dumped geoms & new geom field
-- drop table if exists testing.sa1_2021_aust_gda94_web;
-- create table testing.sa1_2021_aust_gda94_web as (
--     select sa1_code_2021,
--            (st_dump(geom)).*
--     from census_2021_bdys.sa1_2021_aust_gda94
-- );
-- create index sa1_2021_aust_gda94_web_gist on testing.sa1_2021_aust_gda94_web using gist(geom);
-- alter table testing.sa1_2021_aust_gda94_web cluster on sa1_2021_aust_gda94_web_gist;
--
-- -- adds the new geom column that will contain simplified geoms
-- alter table testing.sa1_2021_aust_gda94_web add column simple_geom geometry(POLYGON, 4283);
--
-- -- STEP 2 - create topology
--
-- -- create new empty topology structure
-- -- select DropTopology('topo1');
-- select CreateTopology('topo1', 4283, 0);
--
-- -- add all polygons to topology in one operation as a collection
-- select ST_CreateTopoGeo('topo1', ST_Collect(geom))
-- from census_2021_bdys.sa1_2021_aust_gda94;

