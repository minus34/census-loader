#!/usr/bin/env bash


# downloads ABS Census boundaries in GeoPackage format, and imports them into Postgres/PostgGIS
#
# Arguments:
#   1. The datum of the boundary files: valid values are GDA94 or GDA2020
#
# Sample command line: . /Users/$(whoami)/git/minus34/census-loader/run.sh 2021 GDA94
#

# Edit these to taste
CENSUS_YEAR=2021
DATA_PATH="/Users/$(whoami)/tmp/census_${CENSUS_YEAR}_data"
BDYS_PATH="/Users/$(whoami)/tmp/census_${CENSUS_YEAR}_bdys"

# get the directory this script is running from
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# load both sets of census boundaries
. ${SCRIPT_DIR}/run.sh GDA94
. ${SCRIPT_DIR}/run.sh GDA2020

# load census data
python.exe load-census.py --census-data-path=${DATA_PATH} --census-bdys-path=${BDYS_PATH}
