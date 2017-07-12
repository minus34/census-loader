
psql -d geo -p 5432 -U postgres -c "CREATE EXTENSION IF NOT EXISTS postgis;"

"C:\Program Files\PostgreSQL\9.6\bin\pg_restore" -Fc -d geo -p 5432 -U postgres "C:\git\minus34\census_2011_data.dmp"
"C:\Program Files\PostgreSQL\9.6\bin\pg_restore" -Fc -d geo -p 5432 -U postgres "C:\git\minus34\census_2011_bdys.dmp"
"C:\Program Files\PostgreSQL\9.6\bin\pg_restore" -Fc -d geo -p 5432 -U postgres "C:\git\minus34\census_2011_web.dmp"

pause