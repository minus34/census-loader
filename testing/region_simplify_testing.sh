#!/usr/bin/env bash

## SETUP - download Git repo and build locally (requires Java and Maven)
#cd ${GIT_HOME}
#mkdir -p eurostat
#cd eurostat
#git clone https://github.com/eurostat/RegionSimplify.git
#cd RegionSimplify
#mvn package
#
#BDYS_PATH="/Users/$(whoami)/tmp/census_2021_bdys"
#
#mkdir -p "${BDYS_PATH}/thinned"

# load environment with GDAL
conda deactivate
conda activate geo

cd $GIT_HOME/eurostat/RegionSimplify

# thin each layer and output to geopackage
for dataset in "sa1_2021_aust_gda94"
do
  query="SELECT * FROM census_2021_bdys_gda94.${dataset} WHERE geom IS NOT NULL"

  ogr2ogr -f GeoPackage "${output_folder}/${dataset}.gpkg" \
  PG:"host=localhost dbname=geo user=postgres password=password port=5432" -sql ${query}

#	for scaleM in "5" "10" "20"
#	do
#    	echo "Generalisation for "$dataset" - 1:"$scaleM"000000"
#		java -Xmx12g -Xms4g -jar ./target/RegionSimplify-1.4.0-SNAPSHOT.jar -i "/Users/s57405/tmp/census_2021_bdys/"$dataset".gpkg" -o "/Users/s57405/tmp/census_2021_bdys/thinned/"$dataset"_"$scaleM"m.gpkg" -s $scaleM"000000"
#	done
done



#java -Xmx8g -Xms4g -jar /Users/s57405/Downloads/RegionSimplify/target/RegionSimplify-1.4.0-SNAPSHOT.jar \
#-i "/Users/s57405/tmp/census_2021_bdys/ASGS_2021_Main_Structure_GDA2020.gpkg" \
#-o "/Users/s57405/tmp/census_2021_bdys/thinned/test.gpkg"
#
#
#java -Xmx8g -Xms4g -jar /Users/s57405/Downloads/RegionSimplify/target/RegionSimplify-1.4.0-SNAPSHOT.jar \
#-i "/Users/s57405/tmp/census_2021_bdys/test.shp" \
#-o "/Users/s57405/tmp/census_2021_bdys/thinned/test.shp"


