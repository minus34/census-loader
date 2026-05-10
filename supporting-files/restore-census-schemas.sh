#!/usr/bin/env bash

SECONDS=0*

echo "----------------------------------------------------------------------------------------------------------------"
echo " start dump file restore"
echo "----------------------------------------------------------------------------------------------------------------"

psql -d geo -p 5432 -U postgres -c "CREATE EXTENSION IF NOT EXISTS postgis;"

cd /Users/$(whoami)/Downloads

curl --insecure https://minus34.com/opendata/census-2016/census_2016_data.dmp --output ./census_2016_data.dmp
/Applications/Postgres.app/Contents/Versions/16/bin/pg_restore -Fc -d geo -p 5432 -U postgres ./census_2016_data.dmp
rm ./census_2016_data.dmp

curl --insecure https://minus34.com/opendata/census-2021/census_2021_data.dmp --output ./census_2021_data.dmp
/Applications/Postgres.app/Contents/Versions/16/bin/pg_restore -Fc -d geo -p 5432 -U postgres ./census_2021_data.dmp
rm ./census_2021_data.dmp

curl --insecure https://minus34.com/opendata/census-2021/census_2021_bdys_gda94.dmp --output ./census_2021_bdys_gda94.dmp
/Applications/Postgres.app/Contents/Versions/16/bin/pg_restore -Fc -d geo -p 5432 -U postgres ./census_2021_bdys_gda94.dmp
rm ./census_2021_bdys_gda94.dmp

curl --insecure https://minus34.com/opendata/census-2021/census_2021_bdys_gda2020.dmp --output ./census_2021_bdys_gda2020.dmp
/Applications/Postgres.app/Contents/Versions/16/bin/pg_restore -Fc -d geo -p 5432 -U postgres ./census_2021_bdys_gda2020.dmp
rm ./census_2021_bdys_gda2020.dmp

duration=$SECONDS

echo " End time : $(date)"
echo " it took $((duration / 60)) mins"
echo "----------------------------------------------------------------------------------------------------------------"
