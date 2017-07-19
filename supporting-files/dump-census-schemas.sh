#!/usr/bin/env bash

/Applications/Postgres.app/Contents/Versions/9.6/bin/pg_dump -Fc -d geo -n census_2016_data -p 5432 -U postgres -f ~/tmp/census_2016_data.dmp
/Applications/Postgres.app/Contents/Versions/9.6/bin/pg_dump -Fc -d geo -n census_2016_bdys -p 5432 -U postgres -f ~/tmp/census_2016_bdys.dmp
/Applications/Postgres.app/Contents/Versions/9.6/bin/pg_dump -Fc -d geo -n census_2016_web -p 5432 -U postgres -f ~/tmp/census_2016_web.dmp

#/Applications/Postgres.app/Contents/Versions/9.6/bin/pg_dump -Fd -j 4 -d geo -n census_2016_data -p 5432 -U postgres -f ~/tmp/census_2016_data
#/Applications/Postgres.app/Contents/Versions/9.6/bin/pg_dump -Fd -j 4 -d geo -n census_2016_bdys -p 5432 -U postgres -f ~/tmp/census_2016_bdys
#/Applications/Postgres.app/Contents/Versions/9.6/bin/pg_dump -Fd -j 4 -d geo -n census_2016_web -p 5432 -U postgres -f ~/tmp/census_2016_web
