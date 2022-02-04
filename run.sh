#!/usr/bin/env bash

CENSUS_YEAR="2021"
DATA_PATH="/Users/$(whoami)/tmp/census_2021_data"
BDYS_PATH="/Users/$(whoami)/tmp/census_2021_bdys"

DATA_SCHEMA="census_${CENSUS_YEAR}_data"
BDYS_SCHEMA="census_${CENSUS_YEAR}_bdys"
WEB_SCHEMA="census_${CENSUS_YEAR}_web"

cd ~/git/minus34/census-loader

# load boundaries using OGR (requires GDAL to be installed)
psql -d geo -c "create schema if not exists ${BDYS_SCHEMA};alter schema ${BDYS_SCHEMA} owner to postgres"

cd ${BDYS_PATH}

files=(`find . -name "*.gpkg"`)

echo${files}


for f in ${files};
  do
    echo "Importing ${f}"
    ogr2ogr -f "PostgreSQL" "PG:host=localhost user=postgres dbname=geo password=password port=5432" \
    -a_srs EPSG:4283 -lco OVERWRITE=YES -lco GEOMETRY_NAME=geom -lco SCHEMA=${BDYS_SCHEMA} ${f}
  done


#python.exe load-census.py --census-year=2011 --data-schema=census_2011_data --boundary-schema=census_2011_bdys --web-schema=census_2011_web --census-data-path=~/tmp/abs_census_2011_data --census-bdys-path=~/tmp/abs_census_2011_boundaries
#python.exe load-census.py --census-year=2016 --data-schema=census_2016_data --boundary-schema=census_2016_bdys --web-schema=census_2016_web --census-data-path=~/tmp/abs_census_2016_data --census-bdys-path=~/tmp/abs_census_2016_boundaries
#python.exe load-census.py --census-data-path=${DATA_PATH} --census-bdys-path=${BDYS_PATH}
