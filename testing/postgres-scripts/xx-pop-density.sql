

-- create schema testing;

drop view if exists testing.vw_lga_pop_density;
create view testing.vw_lga_pop_density as
SELECT bdy.lga_code_2021,
       bdy.lga_name_2021,
	   stats.g3,
	   bdy.area_albers_sqkm,
	   (stats.g3::float / bdy.area_albers_sqkm)::numeric(5,1) as pop_density,
	   bdy.geom
FROM census_2021_bdys_gda94.lga_2021_aust_gda94 as bdy
LEFT OUTER JOIN census_2016_data.lga_g01 as stats on bdy.lga_code_2021 = stats.region_id
;




SELECT sequential_id, short_id, long_id, table_number, profile_table, column_heading_description
	FROM census_2016_data.metadata_stats
where left(sequential_id, 1) = 'G'
order by table_number, sequential_id
;

