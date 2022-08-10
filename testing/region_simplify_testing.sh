#!/usr/bin/env bash

## ONE TIME SETUP - download Git repo and build locally (requires Java and Maven)
#cd ${GIT_HOME}
#mkdir -p eurostat
#cd eurostat
#git clone https://github.com/eurostat/RegionSimplify.git
#cd RegionSimplify
#mvn package

BDYS_PATH="/Users/$(whoami)/tmp/census_2021_bdys"

# create output path
mkdir -p "${BDYS_PATH}/thinned"

# load environment with GDAL
conda deactivate
conda activate geo

# thin each layer and output to geopackage
cd $GIT_HOME/eurostat/RegionSimplify

#"ste_2021_aust_gda94" "sa4_2021_aust_gda94" "sa3_2021_aust_gda94" "sa2_2021_aust_gda94" "sa1_2021_aust_gda94"

for dataset in "sa4_2021_aust_gda94"
do
  echo "Exporting ${dataset} to Shapefile"
  ogr2ogr -f GPKG "${BDYS_PATH}/${dataset}.gpkg" \
  PG:"host='localhost' dbname='geo' user='postgres' password='password' port='5432'" -sql "SELECT * FROM census_2021_bdys_gda94.${dataset} WHERE geom IS NOT NULL"

	for scaleM in "1" "3" "5" "7" "9"
	do
    echo "Thinning ${dataset} at 1:${scaleM}000000"
		java -Xmx12g -Xms4g -jar ./target/RegionSimplify-1.4.0-SNAPSHOT.jar -i "${BDYS_PATH}/${dataset}.shp" -o "${BDYS_PATH}//thinned/${dataset}_${scaleM}m.gpkg" -s "${scaleM}000000"

    # load results into PostGIS
    ogr2ogr -f "PostgreSQL" -overwrite -nlt MULTIPOLYGON -nln "testing.${dataset}_${scaleM}m" PG:"host=localhost port=5432 dbname=geo user=postgres password=password" "${BDYS_PATH}//thinned/${dataset}_${scaleM}m.gpkg"
	done
done
