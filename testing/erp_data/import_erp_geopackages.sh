#!/usr/bin/env bash

conda deactivate
conda activate geo

SECONDS=0*

# set Postgres connection string
PG_CONNECT_STRING="PG:host=localhost user=postgres dbname=geo password=password port=5432"

PG_SCHEMA="testing"
GPKG_PATH="/Users/$(whoami)/Downloads"

echo "-------------------------------------------------------------------------"
echo "Importing files into Postgres"
echo "-------------------------------------------------------------------------"

# requires GDAL to be installed
psql -d geo -c "create schema if not exists ${PG_SCHEMA};alter schema ${PG_SCHEMA} owner to postgres"

find ${GPKG_PATH} -name "*.gpkg" > ${GPKG_PATH}/temp.txt

while read f;
  do
    echo "  - Importing ${f}"
    ogr2ogr -f "PostgreSQL" "${PG_CONNECT_STRING}" -lco OVERWRITE=YES -lco GEOMETRY_NAME=geom -lco SCHEMA=${PG_SCHEMA} "${f}"
#    ogr2ogr -f "PostgreSQL" "${PG_CONNECT_STRING}" -a_srs EPSG:4283 -lco OVERWRITE=YES -lco GEOMETRY_NAME=geom -lco SCHEMA=${BDYS_SCHEMA} ${f}
  done < ${GPKG_PATH}/temp.txt

rm ${GPKG_PATH}/temp.txt

duration=$SECONDS
echo "GeoPackages loaded in $((duration / 60)) mins"
