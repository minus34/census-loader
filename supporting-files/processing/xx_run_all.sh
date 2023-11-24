#!/usr/bin/env bash

# Edit these to taste
CENSUS_YEAR=2021
DATA_PATH="/Users/$(whoami)/tmp/census_${CENSUS_YEAR}_data"
BDYS_PATH="/Users/$(whoami)/tmp/census_${CENSUS_YEAR}_bdys"

# get the directory this script is running from
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd ${SCRIPT_DIR}

# start Python environment with GDAL and Psycopg 3
#. 01_setup_conda_env.sh
conda deactivate
conda activate geo

# get the directory this script is running from
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# load both sets of census boundaries
. 02_download_boundaries.sh GDA94
. 02_download_boundaries.sh GDA2020

# download and unzip census datapacks
. 03_download_datapacks.sh

echo "---------------------------------------------------------------------------------------------------------------------"
echo "processing census data"
echo "---------------------------------------------------------------------------------------------------------------------"

# load census data
python ../../load-census.py --census-data-path=${DATA_PATH} --census-bdys-path=${BDYS_PATH}

echo "---------------------------------------------------------------------------------------------------------------------"
echo "creating Postgres dump files and upload to AWS S3"
echo "---------------------------------------------------------------------------------------------------------------------"

# dump from postgres and copy to AWS S3
. ../dump-census-schemas.sh

# create docker images for both datums
. 04_create_docker_images.sh
