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

ogr2ogr -f "PostgreSQL" "PG:database" -t_srs EPSG:4283 -overwrite -lco GEOMETRY_NAME=geom -lco SCHEMA=${BDYS_SCHEMA} /Users/s57405/tmp/census_2021_bdys/ASGS_Ed3_2021_Indigenous_Structure_GDA94_GPKG/ASGS_Ed3_2021_Indigenous_Structure_GDA94.gpkg



#python.exe load-census.py --census-year=2011 --data-schema=census_2011_data --boundary-schema=census_2011_bdys --web-schema=census_2011_web --census-data-path=~/tmp/abs_census_2011_data --census-bdys-path=~/tmp/abs_census_2011_boundaries
#python.exe load-census.py --census-year=2016 --data-schema=census_2016_data --boundary-schema=census_2016_bdys --web-schema=census_2016_web --census-data-path=~/tmp/abs_census_2016_data --census-bdys-path=~/tmp/abs_census_2016_boundaries
#python.exe load-census.py --census-data-path=${DATA_PATH} --census-bdys-path=${BDYS_PATH}
