drop table if exists testing.combined_ucls CASCADE;
create table testing.combined_ucls as
with ucls as (
  select id,
         name,
         population,
         (population::float / 23355119.0 * 100.0)::numeric(4, 1) as percent_population,
         area::integer,
         st_concavehull(st_buffer(geom, 0.00001), 0.999) AS geom
  from census_2016_web.ucl
  where name not LIKE 'Remainder of State/Territory%'
  and population > 1000
)
SELECT * FROM ucls;

analyze testing.combined_ucls;

alter table testing.combined_ucls owner to postgres;

ALTER TABLE testing.combined_ucls ADD CONSTRAINT combined_ucls_pkey PRIMARY KEY (id);

-- create spatial index and optimise
CREATE INDEX combined_ucls_geom_idx ON testing.combined_ucls USING GIST (geom);
ALTER TABLE testing.combined_ucls CLUSTER ON combined_ucls_geom_idx;