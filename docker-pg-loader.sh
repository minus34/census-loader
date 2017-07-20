#!/bin/bash
echo "Starting import script"

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

# Load the data.
python3 load-census.py \
    --census-year 2016 \
	--census-data-path /app/data/ \
	--census-bdys-path /app/data/ \
	--pghost localhost --pgdb census \
	--pguser ${POSTGRES_USER} \
	--pgpassword ${POSTGRES_PASSWORD} \
	--max-processes 2
