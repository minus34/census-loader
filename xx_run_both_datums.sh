#!/usr/bin/env bash

# start Python environment with GDAL and Psycopg2
conda deactivate
conda activate geo

# Edit these to taste
CENSUS_YEAR=2021
DATA_PATH="/Users/$(whoami)/tmp/census_${CENSUS_YEAR}_data"
BDYS_PATH="/Users/$(whoami)/tmp/census_${CENSUS_YEAR}_bdys"

# get the directory this script is running from
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# load both sets of census boundaries
. ${SCRIPT_DIR}/run.sh GDA94
. ${SCRIPT_DIR}/run.sh GDA2020

# download and unzip DataPacKS
. ${SCRIPT_DIR}/download_datapacks.sh

# load census data
python ${SCRIPT_DIR}/load-census.py --census-data-path=${DATA_PATH} --census-bdys-path=${BDYS_PATH}
