

select count(*) as num_geoms,
       sum(st_npoints(geom)),
       sum(st_npoints(ST_SimplifyVW(geom, 640)))
from census_2021_bdys.sa1_2021_aust_gda94


