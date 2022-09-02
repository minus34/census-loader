



-- T3	Tot_persons_C06_P	Total_persons_2006_Census_Persons	T01
-- T6	Tot_persons_C11_P	Total_persons_2011_Census_Persons	T01
-- T9	Tot_persons_C16_P	Total_persons_2016_Census_Persons	T01

-- T205	Med_person_inc_we_C2006	Median_total_personal_income_weekly_Census_year_2006	T02
-- T206	Med_person_inc_we_C2011	Median_total_personal_income_weekly_Census_year_2011	T02
-- T207	Med_person_inc_we_C2016	Median_total_personal_income_weekly_Census_year_2016	T02


-- total income of Australia
SELECT SUM(stats.t205 * pop.t3 * 52.25) AS au_income,
			 SUM(pop.t3) as au_population
	FROM census_2016_data.sa2_t02 AS stats
	INNER JOIN census_2016_data.sa2_t01 AS pop
	ON stats.region_id = pop.region_id;

-- 2006 = $505153066305
-- 2011 = $680961134623
-- 2016 = $844608356842

-- share of income by SA2
SELECT (stats.t205 * pop.t3 * 52.25)/505153066305.0 * 100.0 AS proportion,
  stats.t205 * 52.25 AS median_income,
  pop.t3 AS population
	FROM census_2016_data.sa2_t02 AS stats
	INNER JOIN census_2016_data.sa2_t01 AS pop
	ON stats.region_id = pop.region_id;










select width_bucket(stats.t205 * pop.t1 * 52.25, 0, 1000000000, 19) as buckets,
       count(*)
	FROM census_2016_data.sa2_t02 AS stats
	INNER JOIN census_2016_data.sa2_t01 AS pop
	ON stats.region_id = pop.region_id
	group by buckets
	order by buckets;


WITH drb_stats AS (
	SELECT min(drb) AS min,
				 max(drb) AS max
		FROM census_2016_data.sa2_t02 AS stats
		INNER JOIN census_2016_data.sa2_t01 AS pop
		ON stats.region_id = pop.region_id
),
     histogram as (
   select width_bucket(drb, min, max, 9) as bucket,
          int4range(min(drb), max(drb), '[]') as range,
          count(*) as freq
     from team_stats, drb_stats
 group by bucket
 order by bucket
)
 select bucket, range, freq,
        repeat('■',
               (   freq::float
                 / max(freq) over()
                 * 30
               )::int
        ) as bar
   from histogram;