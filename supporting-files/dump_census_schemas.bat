
"C:\Program Files\PostgreSQL\9.6\bin\pg_dump" -Fc -d geo -n census_2016_data -p 5432 -U postgres > "C:\git\minus34\census_2016_data.dmp"
"C:\Program Files\PostgreSQL\9.6\bin\pg_dump" -Fc -d geo -n census_2016_bdys -p 5432 -U postgres > "C:\git\minus34\census_2016_bdys.dmp"
"C:\Program Files\PostgreSQL\9.6\bin\pg_dump" -Fc -d geo -n census_2016_web -p 5432 -U postgres > "C:\git\minus34\census_2016_web.dmp"

pause