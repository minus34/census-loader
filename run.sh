#!/usr/bin/env bash

# download, unzip, and delete file
function getfile {
  mkdir -p "$2/$1"
  cd "$2/$1"
  curl -O -L --insecure "https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs-edition-3/jul2021-jun2026/access-and-downloads/digital-boundary-files/$1.zip"
  unzip "$1.zip" -d "$2/$1"
  rm "$1.zip"
}

SECONDS=0*

CENSUS_YEAR="2021"
DATA_PATH="/Users/$(whoami)/tmp/census_${CENSUS_YEAR}_data"
BDYS_PATH="/Users/$(whoami)/tmp/census_${CENSUS_YEAR}_bdys"

DATA_SCHEMA="census_${CENSUS_YEAR}_data"
BDYS_SCHEMA="census_${CENSUS_YEAR}_bdys"
WEB_SCHEMA="census_${CENSUS_YEAR}_web"

# boundary Geopackage file names - DO NOT EDIT
MAINBDYFILE="ASGS_2021_MAIN_STRUCTURE_GPKG_GDA94"
INDIGENOUSBDYFILE="ASGS_Ed3_2021_Indigenous_Structure_GDA94_GPKG"
NONABSBDYFILE="ASGS_Ed3_2021_Non_ABS_Structures_GDA94_GPKG"

# download boundaries
getfile "${MAINBDYFILE}" "${BDYS_PATH}"
getfile "${INDIGENOUSBDYFILE}" "${BDYS_PATH}"
getfile "${NONABSBDYFILE}" "${BDYS_PATH}"


# load boundaries using OGR (requires GDAL to be installed)
psql -d geo -c "create schema if not exists ${BDYS_SCHEMA};alter schema ${BDYS_SCHEMA} owner to postgres"

find ${BDYS_PATH} -name "*.gpkg" > ${BDYS_PATH}/temp.txt

while read f;
  do
    echo "Importing ${f}"
    ogr2ogr -f "PostgreSQL" "PG:host=localhost user=postgres dbname=geo password=password port=5432" \
    -a_srs EPSG:4283 -lco OVERWRITE=YES -lco GEOMETRY_NAME=geom -lco SCHEMA=${BDYS_SCHEMA} ${f}
  done < ${BDYS_PATH}/temp.txt

rm ${BDYS_PATH}/temp.txt

duration=$SECONDS
echo "Boundaries loaded in $((duration / 60)) mins"



##cd ~/git/minus34/census-loader
#
##python.exe load-census.py --census-year=2011 --data-schema=census_2011_data --boundary-schema=census_2011_bdys --web-schema=census_2011_web --census-data-path=~/tmp/abs_census_2011_data --census-bdys-path=~/tmp/abs_census_2011_boundaries
##python.exe load-census.py --census-year=2016 --data-schema=census_2016_data --boundary-schema=census_2016_bdys --web-schema=census_2016_web --census-data-path=~/tmp/abs_census_2016_data --census-bdys-path=~/tmp/abs_census_2016_boundaries
##python.exe load-census.py --census-data-path=${DATA_PATH} --census-bdys-path=${BDYS_PATH}
