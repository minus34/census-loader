#!/usr/bin/env bash

psql -d geo -p 5432 -U postgres -c "CREATE EXTENSION IF NOT EXISTS postgis;"

/Applications/Postgres.app/Contents/Versions/14/bin/pg_restore -Fc -d geo -p 5432 -U postgres ~/Downloads/census_2021_data.dmp
/Applications/Postgres.app/Contents/Versions/14/bin/pg_restore -Fc -d geo -p 5432 -U postgres ~/Downloads/census_2021_bdys_gda94.dmp
/Applications/Postgres.app/Contents/Versions/14/bin/pg_restore -Fc -d geo -p 5432 -U postgres ~/Downloads/census_2021_web.dmp
