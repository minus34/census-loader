#!/usr/bin/env bash

psql -d geo -p 5432 -U postgres -c "CREATE EXTENSION IF NOT EXISTS postgis;"

/Applications/Postgres.app/Contents/Versions/9.6/bin/pg_restore -Fc -d geo -p 5432 -U postgres /Users/hugh/tmp/census_2011_data.dmp
/Applications/Postgres.app/Contents/Versions/9.6/bin/pg_restore -Fc -d geo -p 5432 -U postgres /Users/hugh/tmp/census_2011_bdys.dmp
/Applications/Postgres.app/Contents/Versions/9.6/bin/pg_restore -Fc -d geo -p 5432 -U postgres /Users/hugh/tmp/census_2011_web.dmp
