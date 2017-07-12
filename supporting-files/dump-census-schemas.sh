#!/usr/bin/env bash

/Applications/Postgres.app/Contents/Versions/9.6/bin/pg_dump -Fc -d geo -n census_2016_data -p 5432 -U postgres -f /Users/hugh/tmp/census_2011_data.dmp
/Applications/Postgres.app/Contents/Versions/9.6/bin/pg_dump -Fc -d geo -n census_2016_bdys -p 5432 -U postgres -f /Users/hugh/tmp/census_2011_bdys.dmp
/Applications/Postgres.app/Contents/Versions/9.6/bin/pg_dump -Fc -d geo -n census_2016_web -p 5432 -U postgres -f /Users/hugh/tmp/census_2011_web.dmp
