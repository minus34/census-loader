#!/usr/bin/env bash

## ONE TIME SETUP - download Git repo and build locally (requires Java and Maven)
#cd ${GIT_HOME}
#mkdir -p eurostat
#cd eurostat
#git clone https://github.com/eurostat/RegionSimplify.git
#cd RegionSimplify
#mvn package

AWS_PROFILE="minus34"
BDYS_PATH="/Users/$(whoami)/tmp/census_2021_bdys"
OUTPUT_FOLDER="${BDYS_PATH}_thinned"

# create output path


mkdir -p "${OUTPUT_FOLDER}"

# load environment with GDAL
conda deactivate
conda activate geo

# thin each layer and output to geopackage
cd $GIT_HOME/eurostat/RegionSimplify

# "ste_2021_aust_gda94" "sa4_2021_aust_gda94" "sa3_2021_aust_gda94" "sa2_2021_aust_gda94" "sa1_2021_aust_gda94"

#scale=800000
#
#for dataset in "ste_2021_aust_gda94" "sa4_2021_aust_gda94" "sa3_2021_aust_gda94" "sa2_2021_aust_gda94" "sa1_2021_aust_gda94"
#do
#  echo "Exporting ${dataset} to GeoPackage and removing NULL geometries"
#  ogr2ogr -f GPKG "${BDYS_PATH}/${dataset}.gpkg" \
#  PG:"host='localhost' dbname='geo' user='postgres' password='password' port='5432'" \
#  -sql "SELECT * FROM census_2021_bdys_gda94.${dataset} WHERE geom IS NOT NULL"
#
#  echo "Thinning ${dataset} at 1:${scale}"
#
#  filename="${dataset}_${scale}"
#
#  java -Xmx12g -Xms4g -jar ./target/RegionSimplify-1.4.0-SNAPSHOT.jar -i "${BDYS_PATH}/${dataset}.gpkg" \
#  -o "${OUTPUT_FOLDER}/${filename}.gpkg" -s "${scale}" -omcn 256 > /dev/null
#
#  # load results into PostGIS
#  ogr2ogr -f "PostgreSQL" -overwrite -lco geometry_name=geom -nlt MULTIPOLYGON -nln "testing.${filename}" \
#  PG:"host=localhost port=5432 dbname=geo user=postgres password=password" "${OUTPUT_FOLDER}/${filename}.gpkg"
#
#  # output to FlatGeoBuf
#  ogr2ogr -f FlatGeobuf "${OUTPUT_FOLDER}/${filename}.fgb" \
#  PG:"host=localhost port=5432 dbname=geo user=postgres password=password" "testing.${filename}"
#
#  scale=$((scale / 2))
#done


# copy output files to AWS
aws --profile=${AWS_PROFILE} s3 sync ${OUTPUT_FOLDER} s3://minus34.com/opendata/census-2021/geopackage --exclude "*" --include "*.gpkg" --acl public-read
aws --profile=${AWS_PROFILE} s3 sync ${OUTPUT_FOLDER} s3://minus34.com/opendata/census-2021/flatgeobuf --exclude "*" --include "*.fgb" --acl public-read
