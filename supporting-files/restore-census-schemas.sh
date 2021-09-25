#!/usr/bin/env bash

psql -d geo -p 5432 -U postgres -c "CREATE EXTENSION IF NOT EXISTS postgis;"

/Applications/Postgres.app/Contents/Versions/10/bin/pg_restore -Fc -d geo -p 5432 -U postgres ~/Downloads/census_2016_data.dmp
/Applications/Postgres.app/Contents/Versions/10/bin/pg_restore -Fc -d geo -p 5432 -U postgres ~/Downloads/census_2016_bdys.dmp
/Applications/Postgres.app/Contents/Versions/10/bin/pg_restore -Fc -d geo -p 5432 -U postgres ~/Downloads/census_2016_web.dmp
