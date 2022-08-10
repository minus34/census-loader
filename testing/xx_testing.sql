
-- +---------+-----------+----------+----------+----------+
-- |num_geoms|coord_count|avg_coords|min_coords|max_coords|
-- +---------+-----------+----------+----------+----------+
-- |10       |1839295    |204366    |2575      |625504    |
-- +---------+-----------+----------+----------+----------+
select count(*) as num_geoms,
       count(distinct state_code_2021) as num_ids,
       sum(st_npoints(geom)) as coord_count,
       avg(st_npoints(geom))::integer as avg_coords,
       min(st_npoints(geom)) as min_coords,
       max(st_npoints(geom)) as max_coords
from census_2021_bdys_gda94.ste_2021_aust_gda94
where geom is not null
;

-- +---------+-----------+----------+----------+----------+
-- |num_geoms|coord_count|avg_coords|min_coords|max_coords|
-- +---------+-----------+----------+----------+----------+
-- |9        |34018      |3780      |164       |11494     |
-- +---------+-----------+----------+----------+----------+
select count(*) as num_geoms,
       count(distinct state_code_2021) as num_ids,
       sum(st_npoints(geom)) as coord_count,
       avg(st_npoints(geom))::integer as avg_coords,
       min(st_npoints(geom)) as min_coords,
       max(st_npoints(geom)) as max_coords
from testing.ste_2021_aust_gda94_8000000;









select count(*) as num_geoms,
       sum(st_npoints(geom))
--        sum(st_npoints(st_simplifyvw(geom, 0.0000001))),
--        sum(st_npoints(st_simplify(geom, 0.00005))),
--        sum(st_npoints(st_simplifypreservetopology(geom, 0.00005)))
from census_2021_bdys_gda94.ste_2021_aust_gda94
;
