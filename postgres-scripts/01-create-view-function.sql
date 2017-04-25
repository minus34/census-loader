-- Creates a materialised view based on an equation of Census stats input by the user

CREATE OR REPLACE FUNCTION create_census_view(schemaname text, viewname text, equation text, geom_name text) RETURNS void AS 
$BODY$
BEGIN
  EXECUTE 'CREATE OR REPLACE VIEW newView AS ' ||
            'SELECT * FROM func2(' || $1 || ', ' || $2 || ', ' || array_to_string($3, ',') || ')';
  RETURN;
END;
$BODY$ LANGUAGE plpgsql STRICT;





-- create or replace function create_census_view (schemaname text, viewname text, equation text, geom_name text) 
-- returns setof record as $$
--     DECLARE
--         schname alias for $1;
--         tabname alias for $2;
--         tid alias for $3;
--         geo alias for $4;
--         tol alias for $5;
--         numpoints int:=0;
--         time text:='';
--         fullname text := '';
-- 
--     BEGIN
--         IF schname IS NULL OR length(schname) = 0 THEN
--             fullname := quote_ident(tabname);
--         ELSE
--             fullname := quote_ident(schname)||'.'||quote_ident(tabname);
--         END IF;
--         
--         raise notice 'fullname: %', fullname;
-- 
--         EXECUTE 'select sum(st_npoints('||quote_ident(geo)||')), to_char(clock_timestamp(), ''MI:ss:MS'') from '
--             ||fullname into numpoints, time;
--         raise notice 'Num points in %: %. Time: %', tabname, numpoints, time;
--         
--         EXECUTE 'create unlogged table public.poly as ('
--                 ||'select '||quote_ident(tid)||', (st_dump('||quote_ident(geo)||')).* from '||fullname||')';
-- 
--         -- extract rings out of polygons
--         create unlogged table rings as 
--         select st_exteriorRing((st_dumpRings(geom)).geom) as g from public.poly;
--         
--         select to_char(clock_timestamp(), 'MI:ss:MS') into time;
--         raise notice 'rings created: %', time;
--         
--         drop table poly;
-- 
--         -- Simplify the rings. Here, no points further than 10km:
--         create unlogged table gunion as select st_union(g) as g from rings;
--         
--         select to_char(clock_timestamp(), 'MI:ss:MS') into time;
--         raise notice 'union done: %', time;
--         
--         drop table rings;
--         
--         create unlogged table mergedrings as select st_linemerge(g) as g from gunion;
--         
--         select to_char(clock_timestamp(), 'MI:ss:MS') into time;
--         raise notice 'linemerge done: %', time;
--         
--         drop table gunion;
--         
--         create unlogged table simplerings as select st_simplifyPreserveTopology(g, tol) as g from mergedrings;
--         
--         
--         select to_char(clock_timestamp(), 'MI:ss:MS') into time;
--         raise notice 'rings simplified: %', time;
--         
--         drop table mergedrings;
-- 
--         -- extract lines as individual objects, in order to rebuild polygons from these
--         -- simplified lines
--         create unlogged table simplelines as select (st_dump(g)).geom as g from simplerings;
--         
--         drop table simplerings;
-- 
--         -- Rebuild the polygons, first by polygonizing the lines, with a 
--         -- distinct clause to eliminate overlaping segments that may prevent polygon to be created,
--         -- then dump the collection of polygons into individual parts, in order to rebuild our layer. 
--         drop table if exists simplepolys;
--         create  table simplepolys as 
--         select (st_dump(st_polygonize(distinct g))).geom as g
--         from simplelines;
--         
--         select count(*) from simplepolys into numpoints;
--         select to_char(clock_timestamp(), 'MI:ss:MS') into time;
--         raise notice 'rings polygonized. num rings: %. time: %', numpoints, time;
--         
--         drop table simplelines;
-- 
--         -- some spatial indexes
--         create index simplepolys_geom_gist on simplepolys  using gist(g);
-- 
--         raise notice 'spatial index created...';
-- 
--         -- works better: comparing percentage of overlaping area gives better results.
--         -- as input set is multipolygon, we first explode multipolygons into their polygons, to
--         -- be able to find islands and set them the right departement code.
--         RETURN QUERY EXECUTE 'select '||quote_ident(tid)||', st_collect('||quote_ident(geo)||') as geom '
--             ||'from ('
--             --||'    select distinct on (d.'||quote_ident(tid)||') d.'||quote_ident(tid)||', s.g as geom '
--             ||'    select d.'||quote_ident(tid)||', s.g as geom '
--             ||'   from '||fullname||' d, simplepolys s '
--             --||'    where (st_intersects(d.'||quote_ident(geo)||', s.g) or st_contains(d.'||quote_ident(geo)||', s.g))'
--             ||'    where st_intersects(d.'||quote_ident(geo)||', s.g) '
--             ||'    and st_area(st_intersection(s.g, d.'||quote_ident(geo)||'))/st_area(s.g) > 0.5 '
--             ||'    ) as foo '
--             ||'group by '||quote_ident(tid);
--             
--         --drop table simplepolys;
--         
--         RETURN;
--     
--     END;
-- $$ language plpgsql strict;