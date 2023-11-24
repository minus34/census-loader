#!/usr/bin/env bash

# Edit these to taste
CENSUS_YEAR=2021
OUTPUT_FOLDER="/Users/$(whoami)/tmp/census_${CENSUS_YEAR}"
DATA_PATH="${OUTPUT_FOLDER}/data"
BDYS_PATH="${OUTPUT_FOLDER}/bdys"

DATA_SCHEMA="census_${CENSUS_YEAR}_data"
BDYS_SCHEMA="census_${CENSUS_YEAR}_bdys_gda94"
BDYS_2020_SCHEMA="census_${CENSUS_YEAR}_bdys_gda2020"

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
python ../../load-census.py --census-data-path=${DATA_PATH}

#echo "---------------------------------------------------------------------------------------------------------------------"
#echo "creating Postgres dump files and upload to AWS S3"
#echo "---------------------------------------------------------------------------------------------------------------------"
#
## dump from postgres and copy to AWS S3
#. ../dump-census-schemas.sh
#
## create docker images for both datums
#. 04_create_docker_images.sh

#echo "---------------------------------------------------------------------------------------------------------------------"
#echo "create geoparquet versions of Census data & boundary tables and upload to AWS S3"
#echo "---------------------------------------------------------------------------------------------------------------------"
#
## first - activate or create Conda environment with Apache Spark + Sedona
##. /Users/$(whoami)/git/iag_geo/spark_testing/apache_sedona/01_setup_sedona.sh
#
#conda activate sedona
#
## delete all existing files
#rm -rf ${OUTPUT_FOLDER}/geoparquet
#
#python ${SCRIPT_DIR}/../../spark/xx_export_to_geoparquet.py --bdy-schema="${BDYS_SCHEMA}" --output-path="${OUTPUT_FOLDER}/geoparquet"
##python ${SCRIPT_DIR}/../../spark/xx_export_to_geoparquet.py --data-schema="${DATA_SCHEMA}" --bdy-schema="${BDYS_SCHEMA}" --output-path="${OUTPUT_FOLDER}/geoparquet"
#
#aws --profile=${AWS_PROFILE} s3 rm s3://minus34.com/opendata/census-2021/geoparquet/ --recursive
#aws --profile=${AWS_PROFILE} s3 sync ${OUTPUT_FOLDER}/geoparquet s3://minus34.com/opendata/census-2021/geoparquet --acl public-read
