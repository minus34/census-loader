#!/usr/bin/env bash

# downloads ABS Census boundaries in GeoPackage format, and imports them into Postgres/PostgGIS
#
# Arguments:
#   1. Census year: valid value is 2021
#   2. The datum of the boundary files: valid values are GDA94 or GDA2020
#
# Sample command line: . /Users/$(whoami)/git/minus34/census-loader/run.sh 2021 GDA94
#

# function to download, unzip, and delete file
function getfile {
  echo "  - Downloading $1.zip"
  # use insecure to enable through man-in-the-middle proxy servers
  curl -O -L -s --insecure "https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs-edition-3/jul2021-jun2026/access-and-downloads/digital-boundary-files/$1.zip"
  unzip -q "$1.zip" -d "$2"
  rm "$1.zip"
}

SECONDS=0*

# start Python environment with GDAL and Psycopg2
conda deactivate
conda activate geo

# set Postgres connection string
PG_CONNECT_STRING="PG:host=localhost user=postgres dbname=geo password=password port=5432"

# get census year
CENSUS_YEAR=$1

# get datum
DATUM=$(echo $2 | tr '[:lower:]' '[:upper:]')
BDY_SCHEMA_SUFFIX=$(echo ${DATUM} | tr '[:upper:]' '[:lower:]')

DATA_PATH="/Users/$(whoami)/tmp/census_${CENSUS_YEAR}_data"
BDYS_PATH="/Users/$(whoami)/tmp/census_${CENSUS_YEAR}_bdys"

DATA_SCHEMA="census_${CENSUS_YEAR}_data"
BDYS_SCHEMA="census_${CENSUS_YEAR}_bdys_${BDY_SCHEMA_SUFFIX}"
WEB_SCHEMA="census_${CENSUS_YEAR}_web"

# boundary Geopackage file names - DO NOT EDIT
MAINBDYFILE="ASGS_${CENSUS_YEAR}_MAIN_STRUCTURE_GPKG_${DATUM}"
INDIGENOUSBDYFILE="ASGS_Ed3_${CENSUS_YEAR}_Indigenous_Structure_${DATUM}_GPKG"
NONABSBDYFILE="ASGS_Ed3_Non_ABS_Structures_${DATUM}_GPKG_updated_2022"


echo "-------------------------------------------------------------------------"
echo "Downloading ${DATUM} boundary files"
echo "-------------------------------------------------------------------------"

## WARNING: deletes the bdy directory
rm -rf "${BDYS_PATH}"
mkdir -p "${BDYS_PATH}"
cd "${BDYS_PATH}"

getfile "${MAINBDYFILE}" "${BDYS_PATH}"
getfile "${INDIGENOUSBDYFILE}" "${BDYS_PATH}"
getfile "${NONABSBDYFILE}" "${BDYS_PATH}"


echo "-------------------------------------------------------------------------"
echo "Importing ${DATUM} files into Postgres"
echo "-------------------------------------------------------------------------"

# requires GDAL to be installed
psql -d geo -c "create schema if not exists ${BDYS_SCHEMA};alter schema ${BDYS_SCHEMA} owner to postgres"

find ${BDYS_PATH} -name "*_${DATUM}*.gpkg" > ${BDYS_PATH}/temp.txt

while read f;
  do
    echo "  - Importing ${f}"
    ogr2ogr -f "PostgreSQL" "${PG_CONNECT_STRING}" -lco OVERWRITE=YES -lco GEOMETRY_NAME=geom -lco SCHEMA=${BDYS_SCHEMA} ${f}
#    ogr2ogr -f "PostgreSQL" "${PG_CONNECT_STRING}" -a_srs EPSG:4283 -lco OVERWRITE=YES -lco GEOMETRY_NAME=geom -lco SCHEMA=${BDYS_SCHEMA} ${f}
  done < ${BDYS_PATH}/temp.txt

rm ${BDYS_PATH}/temp.txt

duration=$SECONDS
echo "${DATUM} Boundaries loaded in $((duration / 60)) mins"





#https://www.abs.gov.au/census/find-census-data/geopackages/download/Geopackage_2021_G01_AUST_GDA94.zip





##cd ~/git/minus34/census-loader
#
##python.exe load-census.py --census-year=2011 --data-schema=census_2011_data --boundary-schema=census_2011_bdys --web-schema=census_2011_web --census-data-path=~/tmp/abs_census_2011_data --census-bdys-path=~/tmp/abs_census_2011_boundaries
##python.exe load-census.py --census-year=2016 --data-schema=census_2016_data --boundary-schema=census_2016_bdys --web-schema=census_2016_web --census-data-path=~/tmp/abs_census_2016_data --census-bdys-path=~/tmp/abs_census_2016_boundaries
##python.exe load-census.py --census-data-path=~/tmp/abs_census_2021_data --census-bdys-path=~/tmp/abs_census_2021_boundaries


##python.exe load-census.py --census-data-path=${DATA_PATH} --census-bdys-path=${BDYS_PATH}
