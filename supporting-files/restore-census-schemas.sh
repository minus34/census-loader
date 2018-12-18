#!/usr/bin/env bash

psql -d geo -p 5432 -U postgres -c "CREATE EXTENSION IF NOT EXISTS postgis;"

/Applications/Postgres.app/Contents/Versions/10/bin/pg_restore -Fc -d geo -p 5432 -U postgres ~/tmp/census_2016_data.dmp
/Applications/Postgres.app/Contents/Versions/10/bin/pg_restore -Fc -d geo -p 5432 -U postgres ~/tmp/census_2016_bdys.dmp
/Applications/Postgres.app/Contents/Versions/10/bin/pg_restore -Fc -d geo -p 5432 -U postgres ~/tmp/census_2016_web.dmp

#/Applications/Postgres.app/Contents/Versions/9.6/bin/pg_restore -Fd -d geo -p 5432 -U postgres ~/tmp/census_2016_data
#/Applications/Postgres.app/Contents/Versions/9.6/bin/pg_restore -Fd -d geo -p 5432 -U postgres ~/tmp/census_2016_bdys
#/Applications/Postgres.app/Contents/Versions/9.6/bin/pg_restore -Fd -d geo -p 5432 -U postgres ~/tmp/census_2016_web
