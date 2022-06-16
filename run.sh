#!/usr/bin/env bash

# downloads ABS Census 2021 boundaries in GeoPackage format, and imports them into Postgres/PostgGIS
#
# Arguments:
#   1. The datum of the boundary files: valid values are GDA94 or GDA2020
#

# download, unzip, and delete file
function getfile {
  echo "  - Downloading $1.zip"
  mkdir -p "$2"
  cd "$2"
  curl -O -L -s --insecure "https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs-edition-3/jul2021-jun2026/access-and-downloads/digital-boundary-files/$1.zip"
  unzip -q "$1.zip" -d "$2"
  rm "$1.zip"
}

SECONDS=0*

# set Postgres connection string
PG_CONNECT_STRING="PG:host=localhost user=postgres dbname=geo password=password port=5432"

# get datum argument
DATUM=$(echo $1 | tr '[:lower:]' '[:upper:]')

CENSUS_YEAR="2021"
DATA_PATH="/Users/$(whoami)/tmp/census_${CENSUS_YEAR}_data"
BDYS_PATH="/Users/$(whoami)/tmp/census_${CENSUS_YEAR}_bdys"

DATA_SCHEMA="census_${CENSUS_YEAR}_data"
BDYS_SCHEMA="census_${CENSUS_YEAR}_bdys"
WEB_SCHEMA="census_${CENSUS_YEAR}_web"

# boundary Geopackage file names - DO NOT EDIT
MAINBDYFILE="ASGS_2021_MAIN_STRUCTURE_GPKG_${DATUM}"
INDIGENOUSBDYFILE="ASGS_Ed3_2021_Indigenous_Structure_${DATUM}_GPKG"
NONABSBDYFILE="ASGS_Ed3_2021_Non_ABS_Structures_${DATUM}_GPKG"

echo "-------------------------------------------------------------------------"
echo "Downloading boundary files"
echo "-------------------------------------------------------------------------"

getfile "${MAINBDYFILE}" "${BDYS_PATH}"
getfile "${INDIGENOUSBDYFILE}" "${BDYS_PATH}"
getfile "${NONABSBDYFILE}" "${BDYS_PATH}"

echo "-------------------------------------------------------------------------"
echo "Importing into Postgres"
echo "-------------------------------------------------------------------------"

# requires GDAL to be installed
psql -d geo -c "create schema if not exists ${BDYS_SCHEMA};alter schema ${BDYS_SCHEMA} owner to postgres"

find ${BDYS_PATH} -name "*_${DATUM}.gpkg" > ${BDYS_PATH}/temp.txt

while read f;
  do
    echo "  - Importing ${f}"
    ogr2ogr -f "PostgreSQL" "${PG_CONNECT_STRING}" \
    -a_srs EPSG:4283 -lco OVERWRITE=YES -lco GEOMETRY_NAME=geom -lco SCHEMA=${BDYS_SCHEMA} ${f}
  done < ${BDYS_PATH}/temp.txt

rm ${BDYS_PATH}/temp.txt

duration=$SECONDS
echo "${DATUM} Boundaries loaded in $((duration / 60)) mins"


##cd ~/git/minus34/census-loader
#
##python.exe load-census.py --census-year=2011 --data-schema=census_2011_data --boundary-schema=census_2011_bdys --web-schema=census_2011_web --census-data-path=~/tmp/abs_census_2011_data --census-bdys-path=~/tmp/abs_census_2011_boundaries
##python.exe load-census.py --census-year=2016 --data-schema=census_2016_data --boundary-schema=census_2016_bdys --web-schema=census_2016_web --census-data-path=~/tmp/abs_census_2016_data --census-bdys-path=~/tmp/abs_census_2016_boundaries
##python.exe load-census.py --census-data-path=${DATA_PATH} --census-bdys-path=${BDYS_PATH}
