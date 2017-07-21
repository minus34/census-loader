#!/bin/bash
echo "Starting import script"
echo "v1"

# Wait for Postgres to set up the PostGIS tables and accept connections.
CHECK_CMD="psql -h localhost -U ${POSTGRES_USER} -c \dt"
echo "Starting PostGIS to import data..."
(docker-entrypoint.sh postgres &)
n=0
nchecks=10
until [ $n -ge $nchecks ]
do
    let n+=1
    echo "Checking ${n} of ${nchecks} if PostGIS is up..."
    $CHECK_CMD > /dev/null && break
    sleep 5
done
$CHECK_CMD > /dev/null
if [ $? == 0 ]; then
    echo "PostGIS is up and running"
    $CHECK_CMD
else
    echo "PostGIS failed to start"
    exit 1
fi

echo "Waiting for 5 seconds"
sleep 5

# Restore everything
pg_restore -Fc -d ${POSTGRES_USER} -p 5432 -U ${POSTGRES_USER} /tmp/dumps/census_2016_data.dmp
pg_restore -Fc -d ${POSTGRES_USER} -p 5432 -U ${POSTGRES_USER} /tmp/dumps/census_2016_bdys.dmp
pg_restore -Fc -d ${POSTGRES_USER} -p 5432 -U ${POSTGRES_USER} /tmp/dumps/census_2016_web.dmp
